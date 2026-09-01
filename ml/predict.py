"""
GigScore - Prediction Engine

Takes a raw worker profile, applies the same feature-engineering
pipeline used during training, loads the trained bounded Ridge model,
and returns an explainable GigScore.

IMPORTANT:
The model was trained on synthetic data.
The resulting score is a prototype behavioural signal and is NOT
a real-world credit score or calibrated probability of repayment.
"""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


# ============================================================
# Import feature engineering
# ============================================================

# This allows predict.py to work both when:
#
#     python3 ml/predict.py
#
# and when FastAPI imports it as:
#
#     from ml.predict import predict_worker
#
try:
    from ml.feature_engineering import create_features
except ModuleNotFoundError:
    from feature_engineering import create_features


# ============================================================
# Configuration
# ============================================================

MODEL_PATH = Path("models/gigscore_model.joblib")

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


# ============================================================
# Validation
# ============================================================

def validate_worker(worker: dict[str, Any]) -> None:
    """Validate a raw worker profile."""

    required = [
        "worker_id",
        "platform",
        "tenure_months",
        "avg_rating",
        "completion_rate",
        "cancellation_rate",
        "jobs_completed",
        "monthly_income",
        "monthly_jobs",
    ]

    missing = [
        key
        for key in required
        if key not in worker
    ]

    if missing:
        raise ValueError(
            "Missing required fields: "
            + ", ".join(missing)
        )

    if len(worker["monthly_income"]) != 12:
        raise ValueError(
            "monthly_income must contain exactly 12 values."
        )

    if len(worker["monthly_jobs"]) != 12:
        raise ValueError(
            "monthly_jobs must contain exactly 12 values."
        )

    if not 12 <= worker["tenure_months"] <= 60:
        raise ValueError(
            "tenure_months must be between 12 and 60 "
            "for the current prototype."
        )

    if not 3.5 <= worker["avg_rating"] <= 5.0:
        raise ValueError(
            "avg_rating must be between 3.5 and 5.0."
        )

    if not 0.50 <= worker["completion_rate"] <= 1.0:
        raise ValueError(
            "completion_rate must be between 0.50 and 1.0."
        )

    if not 0.0 <= worker["cancellation_rate"] <= 0.35:
        raise ValueError(
            "cancellation_rate must be between 0 and 0.35."
        )

    if any(
        value < 0
        for value in worker["monthly_income"]
    ):
        raise ValueError(
            "Monthly income cannot be negative."
        )

    if any(
        value < 0
        for value in worker["monthly_jobs"]
    ):
        raise ValueError(
            "Monthly jobs cannot be negative."
        )


# ============================================================
# Worker → raw DataFrame
# ============================================================

def worker_to_dataframe(
    worker: dict[str, Any],
) -> pd.DataFrame:
    """Convert a worker dictionary to the raw dataset schema."""

    row = {
        "worker_id": worker["worker_id"],
        "platform": worker["platform"],
        "tenure_months": worker["tenure_months"],
        "avg_rating": worker["avg_rating"],
        "completion_rate": worker["completion_rate"],
        "cancellation_rate": worker["cancellation_rate"],
        "jobs_completed": worker["jobs_completed"],
    }

    for month, income in enumerate(
        worker["monthly_income"],
        start=1,
    ):
        row[f"income_month_{month}"] = income

    for month, jobs in enumerate(
        worker["monthly_jobs"],
        start=1,
    ):
        row[f"jobs_month_{month}"] = jobs

    return pd.DataFrame([row])


# ============================================================
# Score tier
# ============================================================

def get_tier(score: int) -> str:
    """Convert GigScore to a prototype presentation tier."""

    if score >= 800:
        return "Strong"

    if score >= 650:
        return "Moderate-Strong"

    if score >= 500:
        return "Moderate"

    if score >= 350:
        return "Higher Attention"

    return "Limited Evidence"


# ============================================================
# Evidence level
# ============================================================

def get_evidence_level(
    tenure_months: int,
) -> str:
    """
    Describe how much historical evidence supports the score.
    """

    if tenure_months < 6:
        return "Limited"

    if tenure_months < 12:
        return "Developing"

    return "Established"


# ============================================================
# Human-readable explanations
# ============================================================

def feature_explanation(
    feature: str,
    row: pd.Series,
) -> str:
    """Turn a technical feature into a readable explanation."""

    explanations = {

        "tenure_normalized":
            f"{int(row['tenure_months'])} months of platform activity",

        "avg_rating":
            f"{row['avg_rating']:.2f} average platform rating",

        "completion_rate":
            f"{row['completion_rate'] * 100:.1f}% completion rate",

        "cancellation_reliability":
            f"{row['cancellation_rate'] * 100:.1f}% cancellation rate",

        "jobs_completed_log":
            f"{int(row['jobs_completed']):,} lifetime completed jobs",

        "income_mean":
            f"Average monthly income of "
            f"₹{row['income_mean']:,.0f}",

        "income_consistency":
            f"Income consistency of "
            f"{row['income_consistency']:.2f}",

        "income_trend_normalized":
            f"Income trend of "
            f"{row['income_trend_normalized'] * 100:.1f}% "
            f"relative to average income",

        "recent_income_change":
            f"Recent income change of "
            f"{row['recent_income_change'] * 100:.1f}%",

        "work_volume_trend_normalized":
            f"Work-volume trend of "
            f"{row['work_volume_trend_normalized'] * 100:.1f}% "
            f"relative to average volume",

        "average_monthly_jobs":
            f"Average of "
            f"{row['average_monthly_jobs']:.0f} "
            f"completed jobs per month",
    }

    return explanations.get(
        feature,
        feature,
    )


# ============================================================
# Model contribution calculation
# ============================================================

def calculate_feature_contributions(
    model,
    X: pd.DataFrame,
) -> list[dict[str, float]]:
    """
    Estimate feature contributions relative to the model's
    reference point.

    For each feature:

        prediction(actual worker)
        -
        prediction(worker with only this feature moved to
        the scaler's reference mean)

    Positive value:
        feature increases the prediction.

    Negative value:
        feature decreases the prediction.

    These values are explanatory estimates and are NOT
    additive components that must equal the final score.
    """

    # The saved model is a TransformedTargetRegressor.
    #
    # Its underlying StandardScaler + Ridge pipeline
    # is stored in .regressor_.
    pipeline = model.regressor_

    scaler = pipeline.named_steps["scaler"]

    actual_prediction = float(
        model.predict(X)[0]
    )

    contributions = []

    for index, feature in enumerate(
        MODEL_FEATURES
    ):

        reference_X = X.copy()

        # Replace this feature with the population
        # reference value learned by StandardScaler.
        reference_value = (
            scaler.mean_[index]
        )

        reference_X.loc[
            reference_X.index[0],
            feature,
        ] = reference_value

        reference_prediction = float(
            model.predict(reference_X)[0]
        )

        impact = (
            actual_prediction
            - reference_prediction
        )

        contributions.append(
            {
                "feature": feature,
                "impact": float(impact),
            }
        )

    return contributions


# ============================================================
# Prediction
# ============================================================

def predict_worker(
    worker: dict[str, Any],
) -> dict[str, Any]:
    """Generate an explainable GigScore for one worker."""

    validate_worker(worker)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}"
        )

    # --------------------------------------------------------
    # Convert raw worker → DataFrame
    # --------------------------------------------------------

    raw_df = worker_to_dataframe(
        worker
    )

    # --------------------------------------------------------
    # Raw data → engineered features
    # --------------------------------------------------------

    features = create_features(
        raw_df
    )

    X = features[
        MODEL_FEATURES
    ].copy()

    # --------------------------------------------------------
    # Load trained model
    # --------------------------------------------------------

    model = joblib.load(
        MODEL_PATH
    )

    # --------------------------------------------------------
    # Predict reliability
    # --------------------------------------------------------

    reliability = float(
        model.predict(X)[0]
    )

    reliability = float(
        np.clip(
            reliability,
            0.0,
            1.0,
        )
    )

    # Convert to 0–1000 GigScore.
    score = int(
        round(
            reliability * 1000
        )
    )

    tier = get_tier(
        score
    )

    evidence_level = get_evidence_level(
        worker["tenure_months"]
    )

    # --------------------------------------------------------
    # Calculate explanations
    # --------------------------------------------------------

    contributions = calculate_feature_contributions(
        model,
        X,
    )

    # Ignore tiny numerical effects.
    MIN_IMPACT = 0.005

    positive = sorted(
        [
            item
            for item in contributions
            if item["impact"] >= MIN_IMPACT
        ],
        key=lambda item: item["impact"],
        reverse=True,
    )[:3]

    negative = sorted(
        [
            item
            for item in contributions
            if item["impact"] <= -MIN_IMPACT
        ],
        key=lambda item: item["impact"],
    )[:3]

    positive_factors = [
        {
            "feature": item["feature"],
            "impact": round(
                item["impact"] * 1000
            ),
            "explanation": feature_explanation(
                item["feature"],
                features.iloc[0],
            ),
        }
        for item in positive
    ]

    negative_factors = [
        {
            "feature": item["feature"],
            "impact": round(
                item["impact"] * 1000
            ),
            "explanation": feature_explanation(
                item["feature"],
                features.iloc[0],
            ),
        }
        for item in negative
    ]

    # --------------------------------------------------------
    # Human-readable summary
    # --------------------------------------------------------

    if positive_factors and negative_factors:

        summary = (
            f"{tier} observed reliability with "
            "strong positive behavioural signals and "
            "some areas requiring attention."
        )

    elif positive_factors:

        summary = (
            f"{tier} observed reliability with "
            "strong positive behavioural signals."
        )

    elif negative_factors:

        summary = (
            f"{tier} observed reliability with "
            "some behavioural areas requiring attention."
        )

    else:

        summary = (
            f"{tier} observed reliability based on "
            "the available behavioural evidence."
        )

    return {
        "worker_id": worker["worker_id"],
        "score": score,
        "reliability": round(
            reliability,
            4,
        ),
        "tier": tier,
        "evidence_level": evidence_level,
        "summary": summary,
        "positive_factors": positive_factors,
        "risk_factors": negative_factors,
    }


# ============================================================
# Demo worker
# ============================================================

if __name__ == "__main__":

    demo_worker = {
        "worker_id": "DEMO001",
        "platform": "Delivery",
        "tenure_months": 28,
        "avg_rating": 4.8,
        "completion_rate": 0.95,
        "cancellation_rate": 0.03,
        "jobs_completed": 1842,

        "monthly_income": [
            22100,
            23400,
            21900,
            24000,
            23100,
            22800,
            24500,
            25000,
            23900,
            24700,
            25500,
            26100,
        ],

        "monthly_jobs": [
            135,
            142,
            139,
            151,
            148,
            146,
            155,
            159,
            152,
            161,
            165,
            168,
        ],
    }

    result = predict_worker(
        demo_worker
    )

    print(
        "\n=============================="
    )

    print(
        "GIGSCORE RESULT"
    )

    print(
        "=============================="
    )

    print(
        f"\nWorker: {result['worker_id']}"
    )

    print(
        f"Score: {result['score']} / 1000"
    )

    print(
        f"Model reliability estimate: "
        f"{result['reliability']:.4f}"
    )

    print(
        f"Tier: {result['tier']}"
    )

    print(
        f"Evidence: {result['evidence_level']}"
    )

    print(
        f"\nSummary:\n{result['summary']}"
    )

    print(
        "\nPositive contributors:"
    )

    if result["positive_factors"]:

        for factor in result[
            "positive_factors"
        ]:
            print(
                f"+ {factor['explanation']} "
                f"(~{factor['impact']} points)"
            )

    else:
        print("None significant.")

    print(
        "\nRisk contributors:"
    )

    if result["risk_factors"]:

        for factor in result[
            "risk_factors"
        ]:
            print(
                f"- {factor['explanation']} "
                f"(~{factor['impact']} points)"
            )

    else:
        print("None significant.")