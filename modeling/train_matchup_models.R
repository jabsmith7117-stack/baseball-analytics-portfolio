library(dplyr)
library(readr)

set.seed(42)

matchup_data <- read_csv("data/matchup_training_data.csv")

n <- nrow(matchup_data)
train_indices <- sample(seq_len(n), size = 0.8 * n)

train_data <- matchup_data[train_indices, ]
test_data <- matchup_data[-train_indices, ]

cat("Training rows:", nrow(train_data), "\n")
cat("Testing rows:", nrow(test_data), "\n\n")

feature_formula_base <- success ~ platoon_advantage + batter_ops + batter_k_rate + batter_chase_rate +
  batter_hard_hit_rate + batter_whiff_rate +
  pitcher_whiff_rate + pitcher_chase_rate +
  pitcher_hard_hit_rate_allowed + pitcher_k_rate + pitcher_bb_rate

# --- Model 1: Success probability (logistic regression) ---
success_model <- glm(
  feature_formula_base,
  data = train_data,
  family = binomial
)

cat("=== Success Probability Model ===\n")
print(summary(success_model))

test_predictions <- predict(success_model, newdata = test_data, type = "response")
predicted_class <- ifelse(test_predictions >= 0.5, 1, 0)
accuracy <- mean(predicted_class == test_data$success)
cat("\nTest accuracy (0.5 threshold):", round(accuracy, 3), "\n")
cat("Mean predicted prob for actual successes:",
    round(mean(test_predictions[test_data$success == 1]), 3), "\n")
cat("Mean predicted prob for actual non-successes:",
    round(mean(test_predictions[test_data$success == 0]), 3), "\n\n")
    # --- Model 1b: Strikeout probability (logistic regression) ---
k_model <- glm(
  update(feature_formula_base, is_strikeout ~ .),
  data = train_data,
  family = binomial
)

cat("=== Strikeout Probability Model ===\n")
print(summary(k_model))

k_test_predictions <- predict(k_model, newdata = test_data, type = "response")
cat("\nMean predicted prob for actual strikeouts:",
    round(mean(k_test_predictions[test_data$is_strikeout == 1]), 3), "\n")
cat("Mean predicted prob for actual non-strikeouts:",
    round(mean(k_test_predictions[test_data$is_strikeout == 0]), 3), "\n\n")

# --- Model 1c: Walk probability (logistic regression) ---
bb_model <- glm(
  update(feature_formula_base, is_walk ~ .),
  data = train_data,
  family = binomial
)

cat("=== Walk Probability Model ===\n")
print(summary(bb_model))

bb_test_predictions <- predict(bb_model, newdata = test_data, type = "response")
cat("\nMean predicted prob for actual walks:",
    round(mean(bb_test_predictions[test_data$is_walk == 1]), 3), "\n")
cat("Mean predicted prob for actual non-walks:",
    round(mean(bb_test_predictions[test_data$is_walk == 0]), 3), "\n\n")

# --- Model 2: Predicted xwOBA (linear regression) ---
xwoba_formula <- pa_xwoba ~ platoon_advantage + batter_ops + batter_k_rate + batter_chase_rate +
  batter_hard_hit_rate + batter_whiff_rate +
  pitcher_whiff_rate + pitcher_chase_rate +
  pitcher_hard_hit_rate_allowed + pitcher_k_rate + pitcher_bb_rate

xwoba_train <- train_data %>% filter(!is.na(pa_xwoba))
xwoba_test <- test_data %>% filter(!is.na(pa_xwoba))

xwoba_model <- lm(xwoba_formula, data = xwoba_train)

cat("=== Predicted xwOBA Model ===\n")
print(summary(xwoba_model))

xwoba_predictions <- predict(xwoba_model, newdata = xwoba_test)
xwoba_rmse <- sqrt(mean((xwoba_predictions - xwoba_test$pa_xwoba)^2, na.rm = TRUE))
cat("\nTest RMSE:", round(xwoba_rmse, 4), "\n\n")

# --- Model 3: Predicted xBA (linear regression) ---
xba_formula <- pa_xba ~ platoon_advantage + batter_ops + batter_k_rate + batter_chase_rate +
  batter_hard_hit_rate + batter_whiff_rate +
  pitcher_whiff_rate + pitcher_chase_rate +
  pitcher_hard_hit_rate_allowed + pitcher_k_rate + pitcher_bb_rate

xba_train <- train_data %>% filter(!is.na(pa_xba))
xba_test <- test_data %>% filter(!is.na(pa_xba))

xba_model <- lm(xba_formula, data = xba_train)

cat("=== Predicted xBA Model ===\n")
print(summary(xba_model))

xba_predictions <- predict(xba_model, newdata = xba_test)
xba_rmse <- sqrt(mean((xba_predictions - xba_test$pa_xba)^2, na.rm = TRUE))
cat("\nTest RMSE:", round(xba_rmse, 4), "\n\n")

# --- Model 4: Predicted xwOBACON (linear regression, contact only) ---
xwobacon_formula <- pa_xwobacon ~ platoon_advantage + batter_ops + batter_k_rate + batter_chase_rate +
  batter_hard_hit_rate + batter_whiff_rate +
  pitcher_whiff_rate + pitcher_chase_rate +
  pitcher_hard_hit_rate_allowed + pitcher_k_rate + pitcher_bb_rate

xwobacon_train <- train_data %>% filter(is_contact == TRUE, !is.na(pa_xwobacon))
xwobacon_test <- test_data %>% filter(is_contact == TRUE, !is.na(pa_xwobacon))

xwobacon_model <- lm(xwobacon_formula, data = xwobacon_train)

cat("=== Predicted xwOBACON Model (Contact Events Only) ===\n")
print(summary(xwobacon_model))

xwobacon_predictions <- predict(xwobacon_model, newdata = xwobacon_test)
xwobacon_rmse <- sqrt(mean((xwobacon_predictions - xwobacon_test$pa_xwobacon)^2, na.rm = TRUE))
cat("\nTest RMSE:", round(xwobacon_rmse, 4), "\n\n")

saveRDS(success_model, "model/matchup_success_model.rds")
saveRDS(k_model, "model/matchup_k_model.rds")
saveRDS(bb_model, "model/matchup_bb_model.rds")
saveRDS(xwoba_model, "model/matchup_xwoba_model.rds")
saveRDS(xba_model, "model/matchup_xba_model.rds")
saveRDS(xwobacon_model, "model/matchup_xwobacon_model.rds")

cat("All four models saved to /model\n")