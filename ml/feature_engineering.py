"""
GigScore - Feature Engineering

Converts raw synthetic worker data into model-ready behavioural features.

Input:
    data/workers_backup.csv

Output:
    data/features.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_PATH = Path("data/workers_backup.csv")
OUTPUT_PATH = Path("data/features.csv")

INCOME_COLUMNS = [
    f"income_month_{i}"
    for i in range(1, 13)
]

JOBS_COLUMNS = [
    f"jobs_month_{i}"
    for i in range(1, 13)
]


# ============================================================
# Helper functions
# ============================================================

def coefficient_of_variation(values: np.ndarray) -> float:
    """Return income coefficient of variation safely."""

    mean_value = np.mean(values)

    if mean_value <= 0:
        return 0.0

    return float(np.std(values) / mean_value)


def linear_trend(values: np.ndarray) -> float:
    """
    Calculate the slope of a linear regression over the 12 months.
    """

    months = np.arange(1, len(values) + 1)

    return float(
        np.polyfit(months, values, 1)[0]
    )


def recent_change(values: np.ndarray) -> float:
    """
    Compare the latest 3 months with the first 3 months.
    """

    early = np.mean(values[:3])
    recent = np.mean(values[-3:])

    if early <= 0:
        return 0.0

    return float(
        (recent - early) / early
    )


def bounded(value: pd.Series, lower: float, upper: float) -> pd.Series:
    """Bound a pandas Series."""

    return value.clip(lower=lower, upper=upper)


# ============================================================
# Feature creation
# ============================================================

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create the final GigScore model features."""

    result = df[
        [
            "worker_id",
            "platform",
            "tenure_months",
            "avg_rating",
            "completion_rate",
            "cancellation_rate",
            "jobs_completed",
        ]
    ].copy()

    income = df[INCOME_COLUMNS].to_numpy(dtype=float)
    jobs = df[JOBS_COLUMNS].to_numpy(dtype=float)

    # --------------------------------------------------------
    # Basic work features
    # --------------------------------------------------------

    result["tenure_normalized"] = np.clip(
        result["tenure_months"] / 60.0,
        0.0,
        1.0,
    )

    result["cancellation_reliability"] = (
        1.0 - result["cancellation_rate"]
    )

    # Log scaling prevents very large lifetime job counts
    # from dominating the model.
    result["jobs_completed_log"] = np.log1p(
        result["jobs_completed"]
    )

    result["average_monthly_jobs"] = np.mean(
        jobs,
        axis=1,
    )

    # --------------------------------------------------------
    # Income features
    # --------------------------------------------------------

    result["income_mean"] = np.mean(
        income,
        axis=1,
    )

    result["income_volatility"] = np.array([
        coefficient_of_variation(row)
        for row in income
    ])

    result["income_consistency"] = (
        1.0 / (
            1.0 + result["income_volatility"]
        )
    )

    result["income_trend"] = np.array([
        linear_trend(row)
        for row in income
    ])

    # Relative trend rather than raw ₹ / month slope.
    # This makes the feature more comparable across income levels.
    result["income_trend_normalized"] = np.where(
        result["income_mean"] > 0,
        result["income_trend"] / result["income_mean"],
        0.0,
    )

    result["recent_income_change"] = np.array([
        recent_change(row)
        for row in income
    ])

    # --------------------------------------------------------
    # Work-volume trend
    # --------------------------------------------------------

    result["work_volume_trend"] = np.array([
        linear_trend(row)
        for row in jobs
    ])

    result["work_volume_trend_normalized"] = np.where(
        result["average_monthly_jobs"] > 0,
        result["work_volume_trend"]
        / result["average_monthly_jobs"],
        0.0,
    )

    # --------------------------------------------------------
    # Bound potentially extreme ratio features
    # --------------------------------------------------------

    result["income_trend_normalized"] = bounded(
        result["income_trend_normalized"],
        -0.50,
        0.50,
    )

    result["recent_income_change"] = bounded(
        result["recent_income_change"],
        -0.80,
        2.00,
    )

    result["work_volume_trend_normalized"] = bounded(
        result["work_volume_trend_normalized"],
        -0.50,
        0.50,
    )

    # --------------------------------------------------------
    # Final cleanup
    # --------------------------------------------------------

    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    return result


# ============================================================
# Validation
# ============================================================

def validate_features(features: pd.DataFrame) -> None:
    """Validate the generated feature dataset."""

    if features["worker_id"].duplicated().any():
        raise ValueError(
            "Duplicate worker IDs found."
        )

    if features.isnull().any().any():
        missing = features.columns[
            features.isnull().any()
        ].tolist()

        raise ValueError(
            f"Missing values found in: {missing}"
        )

    if not features["tenure_normalized"].between(
        0, 1
    ).all():
        raise ValueError(
            "tenure_normalized outside [0, 1]"
        )

    if not features["cancellation_reliability"].between(
        0, 1
    ).all():
        raise ValueError(
            "cancellation_reliability outside [0, 1]"
        )


# ============================================================
# Main
# ============================================================

def main() -> None:
    """Run feature engineering."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    print(f"Reading: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    required_columns = (
        [
            "worker_id",
            "platform",
            "tenure_months",
            "avg_rating",
            "completion_rate",
            "cancellation_rate",
            "jobs_completed",
        ]
        + INCOME_COLUMNS
        + JOBS_COLUMNS
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

    features = create_features(df)

    validate_features(features)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    features.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nFeature engineering complete.")
    print(f"Saved to: {OUTPUT_PATH}")

    print("\nDataset shape:")
    print(features.shape)

    print("\nColumns:")
    for column in features.columns:
        print(f"  - {column}")

    print("\nFeature summary:")
    print(
        features[
            [
                "tenure_normalized",
                "avg_rating",
                "completion_rate",
                "cancellation_reliability",
                "jobs_completed_log",
                "income_mean",
                "income_volatility",
                "income_consistency",
                "income_trend_normalized",
                "recent_income_change",
                "work_volume_trend_normalized",
                "average_monthly_jobs",
            ]
        ].describe().T[
            ["min", "mean", "max"]
        ]
    )


if __name__ == "__main__":
    main()