# GigScore — API Contract

## Purpose

The backend exposes a simple scoring API for the GigScore frontend.

The frontend sends a worker profile to the backend.

The backend processes the profile through the feature-engineering and
machine-learning pipeline and returns a structured scoring result.

---

## Endpoint

`POST /score`

---

## Request

```json
{
  "worker_id": "W0001",
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
    26100
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
    168
  ]
}

