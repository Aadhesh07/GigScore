"""
GigScore - Model Training

Trains and compares regression models for the synthetic
GigScore reliability target.

IMPORTANT:
The target is synthetic and does not represent real-world
loan repayment probability.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from scipy.special import expit, logit

from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================
# Configuration
# ============================================================

INPUT_PATH = Path("data/training_data.csv")
MODEL_PATH = Path("models/gigscore_model.joblib")

RANDOM_STATE = 42


# ============================================================
# Final model features
# ============================================================

MODEL_FEATURES = [
    "tenure_normalized",
    "avg_rating",
    "completion_rate",
    "cancellation_reliability",
    "jobs_completed_log",
    "income_mean",
    "income_consistency",
    "income_trend_normalized",
    "recent_income_change",
    "work_volume_trend_normalized",
    "average_monthly_jobs",
]

TARGET = "latent_reliability"


# ============================================================
# Bounded Ridge model
# ============================================================

def make_ridge_model():
    """
    Create a Ridge regression model with a logit-transformed target.

    The transformation allows Ridge to operate on an unbounded scale
    while converting predictions back into the valid 0-1 reliability range.
    """

    ridge_pipeline = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                Ridge(
                    alpha=1.0,
                ),
            ),
        ]
    )

    return TransformedTargetRegressor(
        regressor=ridge_pipeline,
        func=logit,
        inverse_func=expit,
    )


# ============================================================
# Evaluation
# ============================================================

def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    name: str,
) -> dict:
    """Evaluate a regression model."""

    predictions = model.predict(
        X_test
    )

    # Safety bound.
    predictions = np.clip(
        predictions,
        0.0,
        1.0,
    )

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions,
        )
    )

    r2 = r2_score(
        y_test,
        predictions,
    )

    print(f"\n{name}")
    print("-" * len(name))

    print(
        f"MAE:  {mae:.4f}"
    )

    print(
        f"RMSE: {rmse:.4f}"
    )

    print(
        f"R²:   {r2:.4f}"
    )

    return {
        "name": name,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:
    """Train, compare and save the GigScore model."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found: {INPUT_PATH}"
        )

    print(
        f"Reading: {INPUT_PATH}"
    )

    df = pd.read_csv(
        INPUT_PATH
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    required_columns = (
        MODEL_FEATURES
        + [TARGET]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(missing_columns)
        )

    # --------------------------------------------------------
    # Prepare input and target
    # --------------------------------------------------------

    X = df[
        MODEL_FEATURES
    ].copy()

    y = df[
        TARGET
    ].copy()

    # --------------------------------------------------------
    # Train / test split
    # --------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=RANDOM_STATE,
        )
    )

    print(
        f"\nTraining samples: {len(X_train):,}"
    )

    print(
        f"Testing samples:  {len(X_test):,}"
    )

    # --------------------------------------------------------
    # Model 1 — Bounded Ridge Regression
    # --------------------------------------------------------

    ridge = make_ridge_model()

    ridge.fit(
        X_train,
        y_train,
    )

    ridge_results = evaluate_model(
        ridge,
        X_test,
        y_test,
        "Bounded Ridge Regression",
    )

    # --------------------------------------------------------
    # Model 2 — Random Forest
    # --------------------------------------------------------

    random_forest = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=4,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    random_forest.fit(
        X_train,
        y_train,
    )

    rf_results = evaluate_model(
        random_forest,
        X_test,
        y_test,
        "Random Forest",
    )

    # --------------------------------------------------------
    # Model selection
    # --------------------------------------------------------

    results = [
        ridge_results,
        rf_results,
    ]

    best = max(
        results,
        key=lambda result: result["r2"],
    )

    print(
        "\n=============================="
    )

    print(
        "MODEL SELECTION"
    )

    print(
        "=============================="
    )

    print(
        f"Selected: {best['name']}"
    )

    print(
        f"Test R²: {best['r2']:.4f}"
    )

    if best["name"] == "Bounded Ridge Regression":
        best_model = ridge
    else:
        best_model = random_forest

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        best_model,
        MODEL_PATH,
    )

    print(
        f"\nSaved model to: {MODEL_PATH}"
    )

    # --------------------------------------------------------
    # Example predictions
    # --------------------------------------------------------

    predictions = np.clip(
        best_model.predict(
            X_test.head(10)
        ),
        0.0,
        1.0,
    )

    print(
        "\nExample predictions:"
    )

    for actual, predicted in zip(
        y_test.head(10),
        predictions,
    ):
        print(
            f"Actual: {actual:.3f}  "
            f"Predicted: {predicted:.3f}  "
            f"GigScore: {round(predicted * 1000)}"
        )


if __name__ == "__main__":
    main()