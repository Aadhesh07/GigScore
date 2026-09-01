# GigScore — Data Dictionary

## Purpose

This document defines the data used by the GigScore prototype.

GigScore uses observable gig-work and financial behaviour to generate an
explainable supplementary signal for lender underwriting.

The hackathon prototype uses synthetic data.

---

## Raw Features

| Feature | Description | Type | Example |
|---|---|---|---:|
| `worker_id` | Unique identifier for the worker | String | W0001 |
| `platform` | Gig platform category | Categorical | Delivery |
| `tenure_months` | Number of months active on the platform | Integer | 28 |
| `avg_rating` | Average platform rating | Float | 4.8 |
| `completion_rate` | Percentage of accepted jobs completed | Float | 0.95 |
| `cancellation_rate` | Percentage of accepted/assigned jobs cancelled | Float | 0.03 |
| `jobs_completed` | Total lifetime number of completed jobs on the platform | Integer | 1842 |
| `monthly_income_1` ... `monthly_income_12` | Monthly earnings over the previous 12 months | Float | 22100 |
| `jobs_month_1` ... `jobs_month_12` | Number of jobs completed each month during the 12-month analysis window | Integer | 154 |
---

## Derived Features

These are calculated from the raw data.

| Feature | Definition | Purpose |
|---|---|---|
| `income_mean` | Mean of the 12 monthly income values | Typical earning level |
| `income_volatility` | Standard deviation ÷ mean income | Relative earnings fluctuation |
| `income_consistency` | `1 / (1 + income_volatility)` | Converts volatility into a higher-is-better stability measure |
| `income_trend` | Trend of monthly income over time | Detects increasing or decreasing earnings |
| `recent_income_change` | Recent earnings compared with an earlier baseline | Captures recent earnings movement |
| `work_volume_trend` | Trend in completed jobs over time | Captures changing work activity |

---

## Feature Engineering

### Income Mean

\[
income\_mean = \frac{1}{12}\sum_{i=1}^{12} income_i
\]

### Income Volatility

We use the coefficient of variation:

\[
income\_volatility =
\frac{\sigma_{income}}{\mu_{income}}
\]

where:

- \(\sigma\) = standard deviation of monthly income
- \(\mu\) = average monthly income

Lower values indicate less relative fluctuation.

### Income Consistency

\[
income\_consistency =
\frac{1}{1 + income\_volatility}
\]

Higher values indicate greater earnings consistency.

### Income Trend

The trend is estimated from the sequence of monthly earnings.

Positive values indicate increasing earnings over time.
Negative values indicate declining earnings.

### Recent Income Change

Recent earnings are compared with the worker's earlier income baseline.

This helps identify recent improvement or deterioration.

### Work Volume Trend

The same principle is applied to completed jobs over time.

---

## Features Excluded

GigScore does not intentionally use protected personal characteristics
as model inputs.

Examples include:

- Religion
- Caste
- Gender
- Race / ethnicity
- Health information
- Political affiliation

The prototype focuses on work and relevant financial behaviour.

---

## Prototype Target

The hackathon prototype does not have access to a large real-world
labelled dataset linking gig-worker behaviour to actual loan outcomes.

Therefore synthetic data will be used for model development.

A synthetic reliability target will be generated from observable
behavioural features with controlled noise.

This target demonstrates the ML pipeline only.

It must not be presented as real-world loan repayment probability.

---

## GigScore Output

The trained model will produce:

\[
P(reliable \mid features)
\]

The prototype GigScore is:

\[
GigScore = 1000 \times P(reliable \mid features)
\]

Example:

\[
P = 0.782
\]

therefore:

\[
GigScore = 782
\]

The score is a prototype supplementary signal and is not an official
credit score.

---

## Product Principle

GigScore does not automatically approve or reject loans.

It provides additional, explainable information that a lender may use
as part of its underwriting process.

