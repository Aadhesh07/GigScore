"""
GigScore - FastAPI Backend

This API exposes the GigScore prediction engine to the frontend.

Run from the GigScore project root:

    uvicorn backend.main:app --reload
"""

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.predict import predict_worker


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
    version="0.1.0",
)


# ============================================================
# CORS
# ============================================================

# Development setting.
# We will restrict this before deployment.
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
        description="Monthly income for the previous 12 months",
    )

    monthly_jobs: List[int] = Field(
        min_length=12,
        max_length=12,
        description="Completed jobs for the previous 12 months",
    )


# ============================================================
# Root endpoint
# ============================================================

@app.get("/")
def root():
    """
    Basic API information.
    """

    return {
        "name": "GigScore API",
        "version": "0.1.0",
        "status": "running",
    }


# ============================================================
# Health endpoint
# ============================================================

@app.get("/health")
def health():
    """
    Health check.
    """

    return {
        "status": "healthy",
        "service": "gigscore-api",
    }


# ============================================================
# Scoring endpoint
# ============================================================

@app.post("/score")
def score_worker(worker: WorkerProfile):
    """
    Calculate a GigScore from a raw worker profile.

    Pipeline:

        request
          ↓
        validation
          ↓
        feature engineering
          ↓
        trained ML model
          ↓
        GigScore + explanation
    """

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