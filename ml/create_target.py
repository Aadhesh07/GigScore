"""
GigScore - Synthetic Reliability Target Generator

Phase 3.3:
Create a synthetic continuous reliability target for ML development.

IMPORTANT:
This target is synthetic and does NOT represent real-world
loan repayment probability.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_PATH = Path("data/features.csv")
OUTPUT_PATH = Path("data/training_data.csv")

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# Helper functions
# ============================================================

def sigmoid(x: np.ndarray) -> np.ndarray:
    """Convert values into the 0–1 range."""
    return 1.0 / (1.0 + np.exp(-x))


def standardize(values: np.ndarray) -> np.ndarray:
    """
    Standardize a numeric array.

    Result:
        mean ≈ 0
        standard deviation ≈ 1
    """
    mean = np.mean(values)
    std = np.std(values)

    if std <= 1e-12:
        return np.zeros_like(values)

    return (values - mean) / std


def create_latent_reliability(
    df: pd.DataFrame,
) -> np.ndarray:
    """
    Create a synthetic continuous reliability target.

    The target is based on observable worker behaviour,
    nonlinear interactions, and controlled noise.

    This is ONLY a synthetic target for demonstrating
    the ML pipeline.
    """

    # --------------------------------------------------------
    # Core behavioural signals
    # --------------------------------------------------------

    tenure = df[
        "tenure_normalized"
    ].to_numpy(dtype=float)

    rating = (
        df["avg_rating"].to_numpy(dtype=float) / 5.0
    )

    completion = df[
        "completion_rate"
    ].to_numpy(dtype=float)

    cancellation_reliability = df[
        "cancellation_reliability"
    ].to_numpy(dtype=float)

    income_consistency = df[
        "income_consistency"
    ].to_numpy(dtype=float)

    # --------------------------------------------------------
    # Work-volume signal
    # --------------------------------------------------------

    jobs_signal = np.clip(
        df["jobs_completed_log"].to_numpy(dtype=float)
        / np.log1p(7000),
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Trend signals
    # --------------------------------------------------------

    income_trend = np.tanh(
        5.0
        * df[
            "income_trend_normalized"
        ].to_numpy(dtype=float)
    )

    work_trend = np.tanh(
        8.0
        * df[
            "work_volume_trend_normalized"
        ].to_numpy(dtype=float)
    )

    # Shift from [-1, 1] to [0, 1].
    income_trend_signal = (
        income_trend + 1.0
    ) / 2.0

    work_trend_signal = (
        work_trend + 1.0
    ) / 2.0

    # --------------------------------------------------------
    # Standardize the signals
    #
    # This prevents the synthetic population from being
    # pushed overwhelmingly toward high reliability.
    # --------------------------------------------------------

    t = standardize(tenure)
    r = standardize(rating)
    c = standardize(completion)
    k = standardize(cancellation_reliability)
    ic = standardize(income_consistency)
    js = standardize(jobs_signal)
    it = standardize(income_trend_signal)
    wt = standardize(work_trend_signal)

    # --------------------------------------------------------
    # Main synthetic behavioural signal
    # --------------------------------------------------------

    z = (
        0.42 * t
        + 0.65 * c
        + 0.45 * r
        + 0.30 * k
        + 0.55 * ic
        + 0.15 * js
        + 0.25 * it
        + 0.20 * wt
    )

    # --------------------------------------------------------
    # Nonlinear effects
    # --------------------------------------------------------

    # Strong completion + strong earnings consistency
    # provides an additional positive interaction.
    z += (
        0.20
        * c
        * ic
    )

    # Excessive instability receives an additional penalty.
    instability = -ic

    z -= (
        0.12
        * instability**2
    )

    # --------------------------------------------------------
    # Recent earnings movement
    # --------------------------------------------------------

    recent_change = np.clip(
        df[
            "recent_income_change"
        ].to_numpy(dtype=float),
        -0.80,
        2.00,
    )

    recent_signal = standardize(
        recent_change
    )

    z += 0.20 * recent_signal

    # --------------------------------------------------------
    # Controlled noise
    #
    # This prevents the target from being a deterministic
    # copy of a hand-written scoring formula.
    # --------------------------------------------------------

    noise = rng.normal(
        loc=0.0,
        scale=0.55,
        size=len(df),
    )

    z += noise

    # --------------------------------------------------------
    # Convert to 0–1
    #
    # The 0.75 multiplier controls how spread out the
    # resulting probabilities are.
    # --------------------------------------------------------

    reliability = sigmoid(
        0.75 * z
    )

    return np.clip(
        reliability,
        0.0,
        1.0,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    """Create the ML training dataset."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    print(f"Reading: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    required_columns = [
        "worker_id",
        "platform",
        "tenure_normalized",
        "avg_rating",
        "completion_rate",
        "cancellation_reliability",
        "jobs_completed_log",
        "income_consistency",
        "income_trend_normalized",
        "recent_income_change",
        "work_volume_trend_normalized",
    ]

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

    # Create synthetic target.
    df["latent_reliability"] = (
        create_latent_reliability(df)
    )

    # Save training data.
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\nSynthetic reliability target created."
    )

    print(
        f"Saved to: {OUTPUT_PATH}"
    )

    print("\nDataset shape:")
    print(df.shape)

    print("\nReliability target summary:")
    print(
        df["latent_reliability"].describe()
    )

    print("\nSample targets:")
    print(
        df[
            [
                "worker_id",
                "latent_reliability",
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()