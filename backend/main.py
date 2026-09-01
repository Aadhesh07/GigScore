"""
GigScore - FastAPI Backend

This API exposes:
1. Worker identity/profile retrieval
2. GigScore prediction

Run from the GigScore project root:

    uvicorn backend.main:app --reload
"""

import csv
import random
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.predict import predict_worker


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

WORKERS_PATH = BASE_DIR / "data" / "workers_backup.csv"
IDENTITY_PATH = BASE_DIR / "data" / "worker_identity.csv"


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="GigScore API",
    description=(
        "API for the GigScore prototype — an explainable "
        "supplementary behavioural signal for gig-worker "
        "credit assessment."
    ),
    version="0.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request model
# ============================================================

class WorkerProfile(BaseModel):
    """
    Raw worker information submitted to GigScore.
    """

    worker_id: str = Field(
        min_length=1,
        description="Unique worker identifier",
    )

    platform: str = Field(
        min_length=1,
        description="Gig platform category",
    )

    tenure_months: int = Field(
        ge=12,
        le=60,
        description="Months active on the platform",
    )

    avg_rating: float = Field(
        ge=3.5,
        le=5.0,
        description="Average platform rating",
    )

    completion_rate: float = Field(
        ge=0.50,
        le=1.0,
        description="Completed jobs divided by accepted jobs",
    )

    cancellation_rate: float = Field(
        ge=0.0,
        le=0.35,
        description="Cancelled jobs divided by accepted jobs",
    )

    jobs_completed: int = Field(
        ge=50,
        description="Lifetime completed jobs",
    )

    monthly_income: List[float] = Field(
        min_length=12,
        max_length=12,
        description="Monthly income for previous 12 months",
    )

    monthly_jobs: List[int] = Field(
        min_length=12,
        max_length=12,
        description="Completed jobs for previous 12 months",
    )


# ============================================================
# Helper: load worker identities
# ============================================================

def load_identities():
    """
    Load worker_id -> name + phone mapping.
    """

    identities = {}

    if not IDENTITY_PATH.exists():
        raise FileNotFoundError(
            f"Identity file not found: {IDENTITY_PATH}"
        )

    with IDENTITY_PATH.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            identities[row["worker_id"]] = {
                "name": row["name"],
                "phone": row["phone"],
            }

    return identities


# ============================================================
# Helper: load workers
# ============================================================

def load_workers():
    """
    Load worker behavioural profiles from the backup dataset.
    """

    if not WORKERS_PATH.exists():
        raise FileNotFoundError(
            f"Worker dataset not found: {WORKERS_PATH}"
        )

    with WORKERS_PATH.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


# ============================================================
# Helper: convert CSV worker to API format
# ============================================================

def convert_worker(row):
    """
    Convert CSV values into the format expected by /score.
    """

    return {
        "worker_id": row["worker_id"],
        "platform": row["platform"],
        "tenure_months": int(row["tenure_months"]),
        "avg_rating": float(row["avg_rating"]),
        "completion_rate": float(row["completion_rate"]),
        "cancellation_rate": float(row["cancellation_rate"]),
        "jobs_completed": int(row["jobs_completed"]),
        "monthly_income": [
            float(row[f"income_m{i}"])
            for i in range(1, 13)
        ],
        "monthly_jobs": [
            int(row[f"jobs_m{i}"])
            for i in range(1, 13)
        ],
    }


# ============================================================
# Root endpoint
# ============================================================

@app.get("/")
def root():

    return {
        "name": "GigScore API",
        "version": "0.2.0",
        "status": "running",
    }


# ============================================================
# Health endpoint
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "gigscore-api",
    }


# ============================================================
# Random worker endpoint
# ============================================================

@app.get("/random-worker")
def random_worker():

    try:
        workers = load_workers()
        identities = load_identities()

        if not workers:
            raise HTTPException(
                status_code=404,
                detail="Worker dataset is empty.",
            )

        # Select a real worker from our synthetic dataset.
        row = random.choice(workers)

        worker = convert_worker(row)

        worker_id = worker["worker_id"]

        identity = identities.get(worker_id)

        if identity is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No identity found for worker "
                    f"{worker_id}."
                ),
            )

        # Add identity information.
        worker["name"] = identity["name"]
        worker["phone"] = identity["phone"]

        return worker

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# Worker lookup endpoint
# ============================================================

@app.get("/worker/{worker_id}")
def get_worker(worker_id: str):

    try:
        workers = load_workers()
        identities = load_identities()

        matching_worker = None

        for row in workers:
            if row["worker_id"] == worker_id:
                matching_worker = row
                break

        if matching_worker is None:
            raise HTTPException(
                status_code=404,
                detail="Worker not found.",
            )

        worker = convert_worker(matching_worker)

        identity = identities.get(worker_id)

        if identity:
            worker["name"] = identity["name"]
            worker["phone"] = identity["phone"]
        else:
            worker["name"] = "Unknown"
            worker["phone"] = "Not available"

        return worker

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# Scoring endpoint
# ============================================================

@app.post("/score")
def score_worker(worker: WorkerProfile):

    result = predict_worker(
        worker.model_dump()
    )

    return result


# ============================================================
# Local development
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )