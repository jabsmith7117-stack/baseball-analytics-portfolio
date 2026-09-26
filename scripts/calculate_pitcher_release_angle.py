import pandas as pd

pitches = pd.read_csv("data/pitcher_data_with_names.csv")

modelable_pitch_types = ["FF", "SI", "SL", "CH", "ST", "FC", "CU", "FS", "KC"]


def release_angle_bucket(angle):
    if pd.isna(angle):
        return None
    if angle >= 65:
        return "Over-The-Top (65°+)"
    if angle >= 45:
        return "High Three-Quarter (45-65°)"
    if angle >= 25:
        return "Three-Quarter (25-45°)"
    if angle >= 5:
        return "Low Three-Quarter / Sidearm (5-25°)"
    return "Submarine / Very Low (<5°)"


release_rows = []

for pitcher_id, pitcher_pitches in pitches.groupby("pitcher"):

    pitcher_name = pitcher_pitches["pitcher_name"].iloc[0]
    current_team = pitcher_pitches["current_team"].iloc[0]
    throws = pitcher_pitches["p_throws"].iloc[0]

    valid_angles = pitcher_pitches["arm_angle"].dropna()

    # Require a much higher pitch count than other splits, and a
    # realistic average velocity - this specifically filters out
    # position players who occasionally pitch in blowouts, whose
    # inconsistent, non-repeatable mechanics would otherwise show up
    # as false "notable release angle variation," the same
    # contamination issue found and fixed in the Stuff+ model.
    avg_velocity = pitcher_pitches["release_speed"].mean()

    if len(valid_angles) < 100 or pd.isna(avg_velocity) or avg_velocity < 65:
        continue

    overall_avg_angle = valid_angles.mean()
    overall_std_angle = valid_angles.std()
    overall_bucket = release_angle_bucket(overall_avg_angle)

    row = {
        "pitcher": pitcher_id,
        "pitcher_name": pitcher_name,
        "current_team": current_team,
        "throws": throws,
        "overall_avg_release_angle": round(overall_avg_angle, 1),
        "overall_release_angle_std": round(overall_std_angle, 1) if pd.notna(overall_std_angle) else None,
        "overall_release_bucket": overall_bucket
    }

    # Per-pitch-type release angle, to see if arm slot shifts
    # noticeably between pitch types (a potential "tell" hitters
    # could pick up on) versus staying consistent (better deception).
    for ptype in modelable_pitch_types:
        ptype_angles = pitcher_pitches[
            pitcher_pitches["pitch_type"] == ptype
        ]["arm_angle"].dropna()

        if len(ptype_angles) >= 15:
            row[f"{ptype}_avg_release_angle"] = round(ptype_angles.mean(), 1)
        else:
            row[f"{ptype}_avg_release_angle"] = None

    release_rows.append(row)

release_df = pd.DataFrame(release_rows)

# Flag pitchers whose release angle varies meaningfully by pitch
# type - a standard deviation above ~5 degrees across their overall
# pitch mix suggests a less consistent slot, worth noting in a
# scouting report as a possible tell.
release_df["notable_angle_variation"] = release_df["overall_release_angle_std"] > 5

release_df = release_df.sort_values("overall_avg_release_angle", ascending=False)

release_df.to_csv("data/pitcher_release_angle_profile.csv", index=False)

print(f"Total pitchers with release angle profile: {len(release_df)}")
print(f"Pitchers with notable angle variation (possible tell): {release_df['notable_angle_variation'].sum()}")
print(
    release_df[
        ["pitcher_name", "overall_avg_release_angle", "overall_release_bucket", "overall_release_angle_std", "notable_angle_variation"]
    ].head(10)
)
print(
    release_df[
        ["pitcher_name", "overall_avg_release_angle", "overall_release_angle_std", "throws"]
    ].sort_values("overall_release_angle_std", ascending=False).head(10)
)