library(dplyr)
library(readr)

pitches <- read_csv("data/hitter_data_with_names.csv")
batter_stats <- read_csv("data/hitter_core_stats.csv")
pitcher_stats <- read_csv("data/pitcher_core_stats.csv")

# Keep only PA-ending pitches - one row per real plate appearance
pa_data <- pitches %>%
  filter(!is.na(woba_denom))

# Define the binary targets: success (hit/walk/HBP), strikeout, walk
pa_data <- pa_data %>%
  mutate(
    success = ifelse(
      events %in% c("single", "double", "triple", "home_run", "walk", "hit_by_pitch"),
      1, 0
    ),
    is_strikeout = ifelse(events == "strikeout", 1, 0),
    is_walk = ifelse(events == "walk", 1, 0),
    is_contact = !is.na(bb_type),
    pa_xwoba = estimated_woba_using_speedangle,
    pa_xba = estimated_ba_using_speedangle,
    # xwOBACON only exists on contact events - NA everywhere else,
    # which is correct, not missing data.
    pa_xwobacon = ifelse(is_contact, estimated_woba_using_speedangle, NA)
  )

# Batter-side features: independent season stats, renamed to avoid
# column-name collisions once merged with pitcher stats.
batter_features <- batter_stats %>%
  select(
    batter,
    batter_ops = ops,
    batter_k_rate = k_rate,
    batter_bb_rate = bb_rate,
    batter_chase_rate = chase_rate,
    batter_hard_hit_rate = hard_hit_rate,
    batter_whiff_rate = whiff_rate,
    batter_season_xwoba = xwoba,
    batter_season_xba = xba,
    batter_season_xwobacon = xwobacon
  )

# Pitcher-side features: independent season stats.
pitcher_features <- pitcher_stats %>%
  select(
    pitcher,
    pitcher_name,
    pitcher_whiff_rate = whiff_rate_induced,
    pitcher_chase_rate = chase_rate_induced,
    pitcher_hard_hit_rate_allowed = hard_hit_rate_allowed,
    pitcher_k_rate = k_rate,
    pitcher_bb_rate = bb_rate,
    pitcher_season_xwoba_against = xwoba_against,
    pitcher_season_xba_against = xba_against,
    pitcher_season_xwobacon_against = xwobacon_against
  )

matchup_data <- pa_data %>%
  inner_join(batter_features, by = "batter") %>%
  inner_join(pitcher_features, by = "pitcher") %>%
  mutate(
    # Platoon advantage: opposite-handed matchups (e.g. RHB vs LHP)
    # traditionally favor the batter, per well-established scouting
    # and sabermetric convention. 1 = opposite-handed (batter
    # advantage), 0 = same-handed.
    platoon_advantage = ifelse(stand != p_throws, 1, 0)
  ) %>%
  select(
    batter, batter_name, pitcher, pitcher_name,
    stand, p_throws, platoon_advantage,
    success, is_strikeout, is_walk, pa_xwoba, pa_xba, pa_xwobacon, is_contact,
    batter_ops, batter_k_rate, batter_bb_rate, batter_chase_rate,
    batter_hard_hit_rate, batter_whiff_rate,
    batter_season_xwoba, batter_season_xba, batter_season_xwobacon,
    pitcher_whiff_rate, pitcher_chase_rate,
    pitcher_hard_hit_rate_allowed, pitcher_k_rate, pitcher_bb_rate,
    pitcher_season_xwoba_against, pitcher_season_xba_against, pitcher_season_xwobacon_against
  )

# A model can't train on rows with missing input features - drop
# any PA where either player lacks a complete season-stat profile.
matchup_data_complete <- matchup_data %>%
  filter(
    !is.na(batter_ops), !is.na(batter_k_rate), !is.na(batter_chase_rate),
    !is.na(batter_hard_hit_rate), !is.na(batter_whiff_rate),
    !is.na(pitcher_whiff_rate), !is.na(pitcher_chase_rate),
    !is.na(pitcher_hard_hit_rate_allowed), !is.na(pitcher_k_rate),
    !is.na(pitcher_bb_rate)
  )

cat("Total PAs before feature-completeness filter:", nrow(matchup_data), "\n")
cat("Total PAs after filter:", nrow(matchup_data_complete), "\n")
cat("Success rate:", round(mean(matchup_data_complete$success), 3), "\n")
cat("Strikeout rate:", round(mean(matchup_data_complete$is_strikeout), 3), "\n")
cat("Walk rate:", round(mean(matchup_data_complete$is_walk), 3), "\n")
cat("PAs with contact (usable for xwOBACON):", sum(matchup_data_complete$is_contact), "\n")
cat("PAs with a valid pa_xwoba value:", sum(!is.na(matchup_data_complete$pa_xwoba)), "\n")

write_csv(matchup_data_complete, "data/matchup_training_data.csv")