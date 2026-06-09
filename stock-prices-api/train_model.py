import pandas as pd
import numpy as np
import mlflow
import mlflow.xgboost
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings

warnings.filterwarnings("ignore")

# Load featured data
df = pd.read_parquet("data_featured.parquet")
print(f"Loaded: {df.shape}")

# Prepare features and target
feature_cols = [col for col in df.columns if col not in ["timestamp", "ticker", "sector", "close"]]
X = df[feature_cols].copy()
y = df["close"].shift(-1)  # Predict next close

# Remove last row (no target)
X = X[:-1]
y = y[:-1]

# Temporal split (80/20)
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"Train: {X_train.shape}, Test: {X_test.shape}")

# MLflow experiment
mlflow.set_experiment("stock_price_prediction")

with mlflow.start_run():
    # Train model
    model = XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Predictions
    y_pred = model.predict(X_test)

    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\nMetrics:")
    print(f"MAE:  ${mae:.2f}")
    print(f"RMSE: ${rmse:.2f}")
    print(f"R²:   {r2:.4f}")

    # Log to MLflow
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("learning_rate", 0.1)
    mlflow.log_metric("mae", mae)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2", r2)

    # Save model
    joblib.dump(model, "stock_price_model.pkl")
    mlflow.xgboost.log_model(model, "model")
    print("\nModel saved: stock_price_model.pkl")
