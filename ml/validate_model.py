"""
GigScore - Cross Validation

Validates the bounded Ridge model across five shuffled folds.

IMPORTANT:
The target is synthetic and does not represent real-world
loan repayment probability.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor


INPUT_PATH = Path("data/training_data.csv")


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


def logit(y):
    """Map (0,1) to the real number line."""

    y = np.asarray(y, dtype=float)

    y = np.clip(
        y,
        1e-5,
        1 - 1e-5,
    )

    return np.log(
        y / (1 - y)
    )


def sigmoid(z):
    """Map real values back to (0,1)."""

    return 1.0 / (
        1.0 + np.exp(-np.asarray(z))
    )


def make_model():
    """Build the same bounded Ridge model used in training."""

    pipeline = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                Ridge(alpha=1.0),
            ),
        ]
    )

    return TransformedTargetRegressor(
        regressor=pipeline,
        func=logit,
        inverse_func=sigmoid,
    )


def main():

    df = pd.read_csv(INPUT_PATH)

    X = df[MODEL_FEATURES]
    y = df[TARGET]

    model = make_model()

    kfold = KFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    r2_scores = cross_val_score(
        model,
        X,
        y,
        cv=kfold,
        scoring="r2",
    )

    mae_scores = -cross_val_score(
        model,
        X,
        y,
        cv=kfold,
        scoring="neg_mean_absolute_error",
    )

    print("5-Fold Cross Validation")
    print("=======================")

    print("\nR² scores:")

    for i, score in enumerate(
        r2_scores,
        start=1,
    ):
        print(
            f"Fold {i}: {score:.4f}"
        )

    print(
        f"\nMean R²: {r2_scores.mean():.4f}"
    )

    print(
        f"R² Std:  {r2_scores.std():.4f}"
    )

    print("\nMAE scores:")

    for i, score in enumerate(
        mae_scores,
        start=1,
    ):
        print(
            f"Fold {i}: {score:.4f}"
        )

    print(
        f"\nMean MAE: {mae_scores.mean():.4f}"
    )

    print(
        f"MAE Std:  {mae_scores.std():.4f}"
    )


if __name__ == "__main__":
    main()