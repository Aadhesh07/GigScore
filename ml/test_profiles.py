"""
GigScore - Profile Sanity Test

Tests the prediction engine against three deliberately different
synthetic worker profiles:

1. Strong worker
2. Mixed / moderate worker
3. Higher-attention worker

This is a behavioural sanity test, not a real credit assessment.
"""

from predict import predict_worker


# ============================================================
# Strong worker
# ============================================================

strong_worker = {
    "worker_id": "TEST_STRONG",

    "platform": "Home Services",

    "tenure_months": 48,

    "avg_rating": 4.92,

    "completion_rate": 0.97,

    "cancellation_rate": 0.02,

    "jobs_completed": 2850,

    "monthly_income": [
        28500,
        29200,
        30100,
        29800,
        30700,
        31500,
        31100,
        32400,
        31900,
        33100,
        33800,
        34500,
    ],

    "monthly_jobs": [
        68,
        71,
        73,
        72,
        75,
        77,
        76,
        79,
        78,
        81,
        83,
        85,
    ],
}


# ============================================================
# Moderate / mixed worker
# ============================================================

moderate_worker = {
    "worker_id": "TEST_MODERATE",

    "platform": "Delivery",

    "tenure_months": 24,

    "avg_rating": 4.35,

    "completion_rate": 0.81,

    "cancellation_rate": 0.12,

    "jobs_completed": 1250,

    "monthly_income": [
        21000,
        23500,
        19800,
        24200,
        22100,
        20700,
        25100,
        22600,
        21800,
        24400,
        23100,
        22500,
    ],

    "monthly_jobs": [
        52,
        60,
        48,
        63,
        57,
        50,
        65,
        55,
        52,
        61,
        57,
        54,
    ],
}


# ============================================================
# Higher-attention worker
# ============================================================

higher_attention_worker = {
    "worker_id": "TEST_ATTENTION",

    "platform": "Ride-Hailing",

    "tenure_months": 12,

    "avg_rating": 3.72,

    "completion_rate": 0.58,

    "cancellation_rate": 0.29,

    "jobs_completed": 620,

    "monthly_income": [
        24000,
        20500,
        22100,
        18000,
        19400,
        16600,
        17500,
        14900,
        15800,
        13200,
        14100,
        11800,
    ],

    "monthly_jobs": [
        61,
        58,
        55,
        52,
        48,
        46,
        43,
        40,
        37,
        34,
        31,
        28,
    ],
}


# ============================================================
# Test runner
# ============================================================

def print_result(
    title: str,
    worker: dict,
) -> None:
    """Run and display one worker's GigScore."""

    result = predict_worker(worker)

    print("\n" + "=" * 55)
    print(title)
    print("=" * 55)

    print(
        f"Worker:       {result['worker_id']}"
    )

    print(
        f"GigScore:     {result['score']} / 1000"
    )

    print(
        f"Reliability:  {result['reliability']:.4f}"
    )

    print(
        f"Tier:         {result['tier']}"
    )

    print(
        f"Evidence:     {result['evidence_level']}"
    )

    print(
        f"Summary:      {result['summary']}"
    )

    print("\nPositive contributors:")

    if result["positive_factors"]:
        for factor in result["positive_factors"]:
            print(
                f"  + {factor['explanation']} "
                f"(~{factor['impact']} points)"
            )
    else:
        print("  None significant.")

    print("\nRisk contributors:")

    if result["risk_factors"]:
        for factor in result["risk_factors"]:
            print(
                f"  - {factor['explanation']} "
                f"(~{factor['impact']} points)"
            )
    else:
        print("  None significant.")


def main() -> None:
    """Run all three profile tests."""

    print_result(
        "1. STRONG WORKER",
        strong_worker,
    )

    print_result(
        "2. MODERATE / MIXED WORKER",
        moderate_worker,
    )

    print_result(
        "3. HIGHER-ATTENTION WORKER",
        higher_attention_worker,
    )


if __name__ == "__main__":
    main()