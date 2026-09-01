"""
GigScore - Random Worker Demo

Selects a random worker from the synthetic dataset
and sends that worker through the real GigScore engine.
"""

import pandas as pd

from predict import predict_worker


DATA_PATH = "data/workers.csv"


def random_worker_from_dataset():
    """Return one randomly selected worker in API-ready format."""

    df = pd.read_csv(DATA_PATH)

    worker = df.sample(1).iloc[0]

    monthly_income = [
        int(worker[f"income_month_{i}"])
        for i in range(1, 13)
    ]

    monthly_jobs = [
        int(worker[f"jobs_month_{i}"])
        for i in range(1, 13)
    ]

    return {
        "worker_id": worker["worker_id"],
        "platform": worker["platform"],
        "tenure_months": int(worker["tenure_months"]),
        "avg_rating": float(worker["avg_rating"]),
        "completion_rate": float(worker["completion_rate"]),
        "cancellation_rate": float(worker["cancellation_rate"]),
        "jobs_completed": int(worker["jobs_completed"]),
        "monthly_income": monthly_income,
        "monthly_jobs": monthly_jobs,
    }


def main():
    worker = random_worker_from_dataset()

    result = predict_worker(worker)

    print("\n========================================")
    print("RANDOM GIG WORKER")
    print("========================================")

    print(f"Worker ID:    {result['worker_id']}")
    print(f"Platform:     {worker['platform']}")
    print(f"Tenure:       {worker['tenure_months']} months")
    print(f"Rating:       {worker['avg_rating']:.2f}")
    print(f"Completion:   {worker['completion_rate']:.1%}")
    print(f"Cancellation: {worker['cancellation_rate']:.1%}")
    print(f"Lifetime jobs:{worker['jobs_completed']:,}")

    print("\n========================================")
    print("GIGSCORE")
    print("========================================")

    print(f"Score:        {result['score']} / 1000")
    print(f"Reliability:  {result['reliability']:.4f}")
    print(f"Tier:         {result['tier']}")
    print(f"Evidence:     {result['evidence_level']}")

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


if __name__ == "__main__":
    main()