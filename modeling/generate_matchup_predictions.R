library(dplyr)
library(readr)
library(tidyr)

batter_stats <- read_csv("data/hitter_core_stats.csv")
pitcher_stats <- read_csv("data/pitcher_core_stats.csv")

success_model <- readRDS("model/matchup_success_model.rds")
k_model <- readRDS("model/matchup_k_model.rds")
bb_model <- readRDS("model/matchup_bb_model.rds")
xwoba_model <- readRDS("model/matchup_xwoba_model.rds")
xba_model <- readRDS("model/matchup_xba_model.rds")
xwobacon_model <- readRDS("model/matchup_xwobacon_model.rds")

batter_features <- batter_stats %>%
  filter(!is.na(bats)) %>%
  select(
    batter, batter_name, current_team, bats,
    batter_ops = ops,
    batter_k_rate = k_rate,
    batter_bb_rate = bb_rate,
    batter_chase_rate = chase_rate,
    batter_hard_hit_rate = hard_hit_rate,
    batter_whiff_rate = whiff_rate,
    batter_season_xwoba = xwoba,
    batter_season_xba = xba,
    batter_season_xwobacon = xwobacon
  ) %>%
  filter(
    !is.na(batter_ops), !is.na(batter_k_rate), !is.na(batter_chase_rate),
    !is.na(batter_hard_hit_rate), !is.na(batter_whiff_rate)
  )

pitcher_features <- pitcher_stats %>%
  filter(!is.na(throws)) %>%
  select(
    pitcher, pitcher_name, current_team, throws,
    pitcher_whiff_rate = whiff_rate_induced,
    pitcher_chase_rate = chase_rate_induced,
    pitcher_hard_hit_rate_allowed = hard_hit_rate_allowed,
    pitcher_k_rate = k_rate,
    pitcher_bb_rate = bb_rate,
    pitcher_season_xwoba_against = xwoba_against,
    pitcher_season_xba_against = xba_against,
    pitcher_season_xwobacon_against = xwobacon_against
  ) %>%
  filter(
    !is.na(pitcher_whiff_rate), !is.na(pitcher_chase_rate),
    !is.na(pitcher_hard_hit_rate_allowed), !is.na(pitcher_k_rate),
    !is.na(pitcher_bb_rate)
  )

cat("Batters with complete features:", nrow(batter_features), "\n")
cat("Pitchers with complete features:", nrow(pitcher_features), "\n")

# Cross join: every batter paired with every pitcher.
all_matchups <- batter_features %>%
  cross_join(pitcher_features) %>%
  mutate(
    platoon_advantage = ifelse(bats != throws, 1, 0)
  )

cat("Total matchup combinations:", nrow(all_matchups), "\n")

all_matchups$predicted_success_probability <- predict(
  success_model, newdata = all_matchups, type = "response"
)
all_matchups$predicted_k_probability <- predict(
  k_model, newdata = all_matchups, type = "response"
)
all_matchups$predicted_bb_probability <- predict(
  bb_model, newdata = all_matchups, type = "response"
)
all_matchups$predicted_xwoba <- predict(xwoba_model, newdata = all_matchups)
all_matchups$predicted_xba <- predict(xba_model, newdata = all_matchups)
all_matchups$predicted_xwobacon <- predict(xwobacon_model, newdata = all_matchups)

final_predictions <- all_matchups %>%
  select(
    batter, batter_name, batter_current_team = current_team.x,
    bats,
    pitcher, pitcher_name, pitcher_current_team = current_team.y,
    throws,
    platoon_advantage,
    predicted_success_probability,
    predicted_k_probability,
    predicted_bb_probability,
    predicted_xwoba,
    predicted_xba,
    predicted_xwobacon,
    batter_season_xwoba,
    batter_season_xba,
    batter_season_xwobacon,
    batter_k_rate,
    batter_bb_rate,
    batter_chase_rate,
    pitcher_season_xwoba_against,
    pitcher_season_xba_against,
    pitcher_season_xwobacon_against,
    pitcher_k_rate,
    pitcher_bb_rate,
    pitcher_chase_rate
  ) %>%
  mutate(
    predicted_success_probability = round(predicted_success_probability, 3),
    predicted_k_probability = round(predicted_k_probability, 3),
    predicted_bb_probability = round(predicted_bb_probability, 3),
    predicted_xwoba = round(predicted_xwoba, 3),
    predicted_xba = round(predicted_xba, 3),
    predicted_xwobacon = round(predicted_xwobacon, 3)
  )

write_csv(final_predictions, "data/matchup_predictions.csv")

cat("\nSaved predictions for", nrow(final_predictions), "matchups\n")
cat("\nSample predictions:\n")
print(head(final_predictions, 10))
cat("\n\nKey prediction columns for the same sample:\n")
print(
  final_predictions %>%
    filter(batter_name == "Yordan Álvarez") %>%
    select(pitcher_name, throws, platoon_advantage, predicted_success_probability, predicted_xwoba) %>%
    head(10)
)