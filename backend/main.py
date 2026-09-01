"""
GigScore - FastAPI Backend

Provides:
1. Worker search
2. Worker profile retrieval
3. GigScore prediction

Run from the GigScore project root:

    uvicorn backend.main:app --reload
"""

import csv
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.predict import predict_worker


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------
# PRIMARY DATASET
#
# The current GigScore generator uses:
#
# income_month_1 ... income_month_12
# jobs_month_1   ... jobs_month_12
#
# Keep workers_backup.csv only as a fallback.
# ------------------------------------------------------------

PRIMARY_WORKERS_PATH = BASE_DIR / "data" / "workers.csv"
BACKUP_WORKERS_PATH = BASE_DIR / "data" / "workers_backup.csv"

IDENTITY_PATH = BASE_DIR / "data" / "worker_identity.csv"


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="GigScore API",
    description=(
        "API for the GigScore prototype — an explainable "
        "supplementary behavioural signal for gig-worker "
        "credit assessment."
    ),
    version="0.4.0",
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
# REQUEST MODEL
# ============================================================

class WorkerProfile(BaseModel):

    worker_id: str = Field(
        min_length=1,
        description="Unique worker identifier",
    )

    platform: str = Field(
        min_length=1,
        description="Gig platform category",
    )

    tenure_months: int = Field(
        ge=0,
        le=120,
        description="Months active on the platform",
    )

    avg_rating: float = Field(
        ge=0.0,
        le=5.0,
        description="Average platform rating",
    )

    completion_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Completed jobs divided by accepted jobs",
    )

    cancellation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Cancelled jobs divided by accepted jobs",
    )

    jobs_completed: int = Field(
        ge=0,
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
# LOAD IDENTITIES
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

            worker_id = row.get("worker_id", "").strip()

            if not worker_id:
                continue

            identities[worker_id] = {
                "name": row.get("name", "").strip(),
                "phone": row.get("phone", "").strip(),
            }

    return identities


# ============================================================
# FIND WORKER DATASET
# ============================================================

def get_workers_path():
    """
    Use the current workers.csv dataset if available.

    Fall back to workers_backup.csv only if workers.csv
    does not exist.
    """

    if PRIMARY_WORKERS_PATH.exists():
        return PRIMARY_WORKERS_PATH

    if BACKUP_WORKERS_PATH.exists():
        return BACKUP_WORKERS_PATH

    raise FileNotFoundError(
        "No worker dataset found. Expected either:\n"
        f"{PRIMARY_WORKERS_PATH}\n"
        f"{BACKUP_WORKERS_PATH}"
    )


# ============================================================
# LOAD WORKERS
# ============================================================

def load_workers():
    """
    Load behavioural worker profiles.
    """

    workers_path = get_workers_path()

    with workers_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

    return rows


# ============================================================
# MONTHLY VALUE HELPERS
# ============================================================

def get_monthly_income(row, month):
    """
    Read monthly income.

    Current dataset:
        income_month_1 ... income_month_12

    Legacy dataset:
        income_m1 ... income_m12
    """

    current_key = f"income_month_{month}"
    legacy_key = f"income_m{month}"

    value = row.get(current_key)

    if value is None or value == "":
        value = row.get(legacy_key)

    if value is None or value == "":
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def get_monthly_jobs(row, month):
    """
    Read monthly completed jobs.

    Current dataset:
        jobs_month_1 ... jobs_month_12

    Legacy dataset:
        jobs_m1 ... jobs_m12
    """

    current_key = f"jobs_month_{month}"
    legacy_key = f"jobs_m{month}"

    value = row.get(current_key)

    if value is None or value == "":
        value = row.get(legacy_key)

    if value is None or value == "":
        return 0

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


# ============================================================
# SAFE INTEGER
# ============================================================

def safe_int(value, default=0):

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# CONVERT CSV WORKER
# ============================================================

def convert_worker(row):

    monthly_income = [
        get_monthly_income(row, month)
        for month in range(1, 13)
    ]

    monthly_jobs = [
        get_monthly_jobs(row, month)
        for month in range(1, 13)
    ]

    return {
        "worker_id": row.get("worker_id", "").strip(),

        "platform": row.get(
            "platform",
            "Unknown",
        ).strip(),

        "tenure_months": safe_int(
            row.get("tenure_months")
        ),

        "avg_rating": safe_float(
            row.get("avg_rating")
        ),

        "completion_rate": safe_float(
            row.get("completion_rate")
        ),

        "cancellation_rate": safe_float(
            row.get("cancellation_rate")
        ),

        "jobs_completed": safe_int(
            row.get("jobs_completed")
        ),

        "monthly_income": monthly_income,

        "monthly_jobs": monthly_jobs,
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "GigScore API",
        "version": "0.4.0",
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "gigscore-api",
    }


# ============================================================
# DATASET STATUS
# ============================================================

@app.get("/debug/dataset")
def dataset_status():

    workers_path = get_workers_path()

    workers = load_workers()

    if not workers:
        return {
            "dataset": str(workers_path),
            "workers": 0,
            "status": "empty",
        }

    first_worker = workers[0]

    income_columns = [
        key
        for key in first_worker.keys()
        if "income" in key.lower()
    ]

    jobs_columns = [
        key
        for key in first_worker.keys()
        if "jobs" in key.lower()
    ]

    return {
        "dataset": str(workers_path),
        "workers": len(workers),
        "income_columns": income_columns,
        "jobs_columns": jobs_columns,
        "status": "loaded",
    }


# ============================================================
# SEARCH WORKERS
# ============================================================

@app.get("/search")
def search_workers(
    q: str = Query(
        ...,
        min_length=1,
        description="Worker name, phone number, or worker ID",
    )
):

    try:

        workers = load_workers()
        identities = load_identities()

        query = q.strip().lower()

        if not query:
            return {
                "workers": []
            }

        results = []

        for row in workers:

            worker_id = row.get(
                "worker_id",
                ""
            ).strip()

            identity = identities.get(worker_id)

            if identity is None:
                continue

            name = identity.get(
                "name",
                ""
            )

            phone = identity.get(
                "phone",
                ""
            )

            searchable_values = [
                name.lower(),
                phone.lower(),
                worker_id.lower(),
            ]

            if any(
                query in value
                for value in searchable_values
            ):

                results.append({
                    "worker_id": worker_id,
                    "name": name,
                    "phone": phone,
                    "platform": row.get(
                        "platform",
                        "Unknown",
                    ),
                    "tenure_months": safe_int(
                        row.get("tenure_months")
                    ),
                })

        results = results[:8]

        return {
            "workers": results
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# WORKER PROFILE
# ============================================================

@app.get("/worker/{worker_id}")
def get_worker(worker_id: str):

    try:

        workers = load_workers()
        identities = load_identities()

        matching_worker = None

        requested_id = worker_id.strip().lower()

        for row in workers:

            current_id = row.get(
                "worker_id",
                ""
            ).strip()

            if current_id.lower() == requested_id:

                matching_worker = row
                break

        if matching_worker is None:

            raise HTTPException(
                status_code=404,
                detail="Worker not found.",
            )

        worker = convert_worker(
            matching_worker
        )

        identity = identities.get(
            worker["worker_id"]
        )

        if identity:

            worker["name"] = identity.get(
                "name",
                "Unknown",
            )

            worker["phone"] = identity.get(
                "phone",
                "Not available",
            )

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
# SCORE
# ============================================================

@app.post("/score")
def score_worker(worker: WorkerProfile):

    try:

        result = predict_worker(
            worker.model_dump()
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )