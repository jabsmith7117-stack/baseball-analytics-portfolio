"""Pull Statcast through a completed game date, retaining existing seasons."""
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from pybaseball import cache, statcast


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", type=date.fromisoformat,
                        default=datetime.utcnow().date() - timedelta(days=1))
    args = parser.parse_args()
    if not date(2026, 3, 25) <= args.through < datetime.utcnow().date():
        parser.error("--through must be a completed date in the 2026 season")
    cache.enable()
    output = Path("data/statcast_2023_2026_full.csv")
    output.parent.mkdir(exist_ok=True)
    combined = pd.read_csv(output, low_memory=False) if output.exists() else None
    if combined is None:
        ranges = [(date(2023, 3, 30), date(2023, 10, 1)),
                  (date(2024, 3, 28), date(2024, 9, 29)),
                  (date(2025, 3, 27), date(2025, 9, 28)),
                  (date(2026, 3, 25), args.through)]
    else:
        keys = {"game_pk", "at_bat_number", "pitch_number", "game_date", "game_year"}
        if not keys.issubset(combined.columns):
            raise ValueError(f"Existing raw file lacks {keys - set(combined.columns)}")
        latest = date.fromisoformat(str(combined.loc[combined.game_year == 2026, "game_date"].max())[:10])
        if latest >= args.through:
            print(f"Existing file already includes games through {latest}.")
            return
        ranges = [(latest + timedelta(days=1), args.through)]
    chunks = []
    for start, end in ranges:
        print(f"Fetching {start} through {end}", flush=True)
        chunk = statcast(start_dt=str(start), end_dt=str(end))
        if chunk.empty:
            raise RuntimeError(f"No pitches returned for {start} through {end}; original file unchanged")
        chunks.append(chunk)
        print(f"Fetched {len(chunk):,} pitches", flush=True)
    result = pd.concat(([combined] if combined is not None else []) + chunks, ignore_index=True)
    result = result.drop_duplicates(subset=["game_pk", "at_bat_number", "pitch_number"])
    latest = result.loc[result.game_year == 2026, "game_date"].max()
    temporary = output.with_suffix(".tmp.csv")
    result.to_csv(temporary, index=False)
    temporary.replace(output)
    print(f"Saved {len(result):,} pitches; latest 2026 game: {latest}")


if __name__ == "__main__":
    main()
