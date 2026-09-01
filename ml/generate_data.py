"""
GigScore - Synthetic Worker Data Generator

Phase 3:
Generate realistic synthetic gig-worker profiles for development.

This file does NOT train the ML model.
It only creates the raw worker dataset that we will use later.
"""

import os

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

NUM_WORKERS = 10_000
OUTPUT_PATH = "data/workers.csv"

# Makes results reproducible.
RANDOM_SEED = 42

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# Generate worker data
# ============================================================

def generate_workers(num_workers: int) -> pd.DataFrame:
    """Generate synthetic raw gig-worker profiles."""

    workers = pd.DataFrame({
        "worker_id": [
            f"W{i:05d}"
            for i in range(1, num_workers + 1)
        ],

        "platform": rng.choice(
            [
                "Delivery",
                "Ride-Hailing",
                "Home Services",
                "Freelance",
            ],
            size=num_workers,
            p=[0.40, 0.25, 0.20, 0.15],
        ),

        # For this prototype, every worker has at least
        # 12 months of history so our 12-month analysis
        # window is fully observed.
        "tenure_months": np.clip(
            rng.gamma(
                shape=3.0,
                scale=8.0,
                size=num_workers,
            ),
            12,
            60,
        ).round().astype(int),

        # Platform rating: 3.5 to 5.0.
        "avg_rating": np.clip(
            rng.normal(
                loc=4.55,
                scale=0.25,
                size=num_workers,
            ),
            3.5,
            5.0,
        ).round(2),

        # Completion rate: 50% to 100%.
        "completion_rate": np.clip(
            rng.beta(
                a=9,
                b=2,
                size=num_workers,
            ),
            0.50,
            1.00,
        ).round(3),

        # Cancellation rate: 0% to 35%.
        "cancellation_rate": np.clip(
            rng.beta(
                a=2,
                b=10,
                size=num_workers,
            ),
            0.00,
            0.35,
        ).round(3),
    })

    # ========================================================
    # Worker-specific work volume
    # ========================================================

    base_jobs_per_month = np.clip(
        rng.normal(
            loc=55,
            scale=18,
            size=num_workers,
        ),
        15,
        120,
    )

    # Small individual growth/decline in work activity.
    job_growth_rate = rng.normal(
        loc=0.0,
        scale=0.003,
        size=num_workers,
    )

    # Give each worker their own seasonal phase.
    # This prevents everyone from having the exact
    # same seasonal pattern.
    job_seasonal_phase = rng.uniform(
        0,
        2 * np.pi,
        size=num_workers,
    )

    # ========================================================
    # Lifetime completed jobs
    # ========================================================

    workers["jobs_completed"] = np.clip(
        workers["tenure_months"]
        * base_jobs_per_month
        * rng.normal(
            loc=1.0,
            scale=0.08,
            size=num_workers,
        ),
        50,
        None,
    ).round().astype(int)

    # ========================================================
    # Worker-specific income characteristics
    # ========================================================

    income_base = rng.lognormal(
        mean=np.log(22_000),
        sigma=0.35,
        size=num_workers,
    )

    worker_volatility = rng.uniform(
        0.05,
        0.35,
        size=num_workers,
    )

    # Each worker gets an independent long-term trend.
    #
    # Positive → gradual earnings growth
    # Negative → gradual earnings decline
    income_growth_rate = rng.normal(
        loc=0.0,
        scale=0.004,
        size=num_workers,
    )

    # Each worker gets a different seasonal phase.
    income_seasonal_phase = rng.uniform(
        0,
        2 * np.pi,
        size=num_workers,
    )

    # ========================================================
    # Generate 12 months of income
    # ========================================================

    for month in range(1, 13):

        month_position = month - 6.5

        # Individual seasonal cycle.
        seasonal_factor = (
            1
            + 0.08
            * np.sin(
                (month / 12) * 2 * np.pi
                + income_seasonal_phase
            )
        )

        # Individual long-term trend.
        trend_factor = np.exp(
            income_growth_rate
            * month_position
        )

        # Individual month-to-month randomness.
        monthly_noise = rng.normal(
            loc=0,
            scale=worker_volatility,
            size=num_workers,
        )

        income = (
            income_base
            * seasonal_factor
            * trend_factor
            * (1 + monthly_noise)
        )

        workers[f"income_month_{month}"] = np.clip(
            income,
            5_000,
            100_000,
        ).round().astype(int)

    # ========================================================
    # Generate 12 months of completed jobs
    # ========================================================

    for month in range(1, 13):

        month_position = month - 6.5

        seasonal_jobs = (
            1
            + 0.06
            * np.sin(
                (month / 12) * 2 * np.pi
                + job_seasonal_phase
            )
        )

        trend_factor = np.exp(
            job_growth_rate
            * month_position
        )

        jobs = (
            base_jobs_per_month
            * seasonal_jobs
            * trend_factor
            * rng.normal(
                loc=1.0,
                scale=0.12,
                size=num_workers,
            )
        )

        workers[f"jobs_month_{month}"] = np.clip(
            jobs,
            1,
            250,
        ).round().astype(int)

    return workers


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    df = generate_workers(NUM_WORKERS)

    os.makedirs("data", exist_ok=True)

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"Generated {len(df):,} synthetic workers."
    )

    print(
        f"Saved to: {OUTPUT_PATH}"
    )

    print("\nDataset shape:")
    print(df.shape)

    print("\nFirst 5 workers:")
    print(df.head())