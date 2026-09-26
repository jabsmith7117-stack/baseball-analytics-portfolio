# Baseball Analytics Portfolio

A four-page Streamlit project exploring MLB scouting, pitcher arsenals, batter-pitcher matchups, and player comparisons. Built from Statcast data with Python, R, SQL/SQLite, and Plotly.

## What is in the app

- **Advanced Scouting Report:** hitter and pitcher tendencies across platoon, pitch type, location, count, release angle, and velocity.
- **Pitcher Arsenal / Stuff+:** pitch-type summaries and visualizations of a custom model's outputs.
- **Batter-Pitcher Matchup Predictor:** matchup probabilities and expected metrics from R regression models, with sequence and tendency views.
- **Scouting Comparison Tool:** SQLite-backed player comparisons and observed versus expected production gaps.

## Source layout

- `app.py` (navigation), `home.py`, `pages/`, `report_helpers.py`: Streamlit user interface.
- `scripts/`: Statcast acquisition, cleaning, feature preparation, split aggregation, and SQLite population.
- `modeling/`: R matchup models plus Python Stuff+, Pitching+, and whiff-model training and scoring scripts; `results/` contains small training summary tables.
- `sql/schema_real.sql`: SQLite schema.

## Run the app

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Share a team-specific opening link

Deploy `app.py` from this repository on Streamlit Community Cloud. The public
app URL works in a browser without installing the code. Append `?team=CLE`
for a Cleveland opening view or `?team=ATH` for an Athletics opening view
(use the team abbreviations shown in the app's selectors). The link sets the
initial team selection and team-inspired colors across the site; reviewers
can still select every other team. It does not change the statistics or model.
The comparison tool spans all teams and keeps its own filters. Opening a new
link in a fresh browser session applies that link's team.

The repository includes processed CSVs read by the four app pages and a SQLite database at `sql/baseball_real.db`. The app reads these outputs directly; R is needed only to retrain the matchup models. Raw Statcast pulls, intermediate data, and model binaries are not committed.

This published snapshot uses 2026 Statcast data refreshed through September 23, 2026. It will not update automatically. The acquisition script accepts `--through YYYY-MM-DD`; refreshing the raw pitches alone does **not** refresh the website tables, matchup predictions, Stuff+ scores, or database. The repository includes the individual processing scripts, while large intermediate files and fitted models remain local. The Stuff+ scoring script's output filename still contains `2025` even when its input spans 2023–2026; the displayed summary pools those seasons.

The arsenal page filters the displayed pitchers to those in the 2026 roster snapshot. Its Stuff+ summary pools multiple seasons and has no season field, so it cannot show 2026-only pitch grades from this file. The grade is custom to this project and should not be compared directly with a published Stuff+ metric.

The core-stat generation script identifies switch hitters, and matchup views use the batter's opposite side from the selected pitcher's throwing hand. Players with limited 2026 appearances may appear in some views but lack qualified comparison or matchup estimates.

## Methods and interpretation

The matchup scripts fit logistic regressions for reaching base, strikeouts, and walks, and linear regressions for xwOBA, xBA, and xwOBACON with a random 80/20 train/test split. The source includes held-out accuracy and RMSE checks. The Stuff+ training script fits pitch-type XGBoost regressors on pitch characteristics using a random 80/20 pitch split; its recorded held-out RMSE values appear in `modeling/results/training_results.csv`. Pitching+ additionally uses location and count, with results in `modeling/results/pitching_plus_training_results.csv`. A random pitch or plate-appearance split is not evidence of future-season or unseen-player forecasting accuracy; time-based and player-aware validation would be valuable next steps. Stuff+ is the project's custom score and should not be treated as an official or directly comparable public metric. Observed-versus-expected gaps are exploratory leads, not proof that a player is undervalued.

Data source: MLB Statcast accessed using `pybaseball`. This repository does not redistribute raw Statcast data.
