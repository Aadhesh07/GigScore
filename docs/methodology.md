# GigScore — Methodology

## 1. Objective

GigScore converts observable gig-work and relevant financial behaviour
into an explainable supplementary signal for lender underwriting.

The prototype does not approve or reject loans.

---

## 2. Overall Pipeline

```text
Raw Worker Data
      ↓
Feature Engineering
      ↓
Data Validation
      ↓
Preprocessing / Scaling
      ↓
ML Model
      ↓
Reliability Probability
      ↓
GigScore (0–1000)
      ↓
Explanation Layer
      ↓
Lender Dashboard

---

## 18. Edge-Case Handling

### Insufficient History

Workers with fewer than 12 months of history will not have missing
months treated as zero income.

The system will distinguish between:

- Limited evidence
- Developing evidence
- Established evidence

### Zero Income

Income volatility must not divide by zero.

If the calculated mean income is zero, volatility will be handled using
a defined fallback rather than producing an invalid value.

### Missing Rating

A missing rating will not automatically be interpreted as a zero rating.

### Missing Behavioural Data

Missing information should be represented explicitly and handled during
preprocessing rather than automatically treated as negative behaviour.

### Extreme Values

Income and activity outliers will be checked during data validation.
Extreme observations will not automatically be removed unless they are
identified as invalid or impossible values.

### New Workers

Workers with very short platform histories may receive a lower evidence
level even when their observed score is strong.

The evidence level is separate from the GigScore itself.



---

## 19. Synthetic Reliability Target Generation

Because the prototype does not have access to real labelled loan-repayment
outcomes, we create a synthetic reliability target for model development.

This target represents the strength of a worker's observed work and
earnings behaviour. It is not real-world loan repayment probability.

### 19.1 Core Behavioural Component

The core behavioural signal is:

\[
Z_{core} =
0.30T +
0.25C +
0.18R +
0.10K +
0.17IC
\]

Where:

- \(T\) = normalised tenure
- \(C\) = completion rate
- \(R\) = normalised rating
- \(K\) = cancellation-adjusted reliability
- \(IC\) = income consistency

### 19.2 Work and Financial Trajectory

Trajectory information is then added:

\[
Z_{trajectory} =
Z_{core} +
0.08IT_n +
0.07WT_n
\]

Where:

- \(IT_n\) = normalised income trend
- \(WT_n\) = normalised work-volume trend

### 19.3 Nonlinear Effects

Small nonlinear terms are introduced so the synthetic target is not
perfectly linear:

\[
Z_{nonlinear} =
Z_{trajectory}
+
0.05C^2
-
0.04V^2
\]

Where:

- \(C\) = completion rate
- \(V\) = normalised income volatility

### 19.4 Controlled Noise

Real-world behaviour is not perfectly deterministic, so controlled random
noise is added:

\[
Z_{noisy} = Z_{nonlinear} + \epsilon
\]

where \(\epsilon\) is sampled from a small zero-centred distribution.

### 19.5 Final Latent Reliability

The final synthetic reliability value is constrained to the range 0–1:

\[
\boxed{
L = clip(Z_{noisy},0,1)
}
\]

This value is called `latent_reliability`.

It is hidden from the final user and is used only as the synthetic target
during model development.

---

## 20. Model Target

The machine learning model learns:

\[
L \approx f(X)
\]

where:

- \(X\) = engineered worker features
- \(L\) = synthetic latent reliability

The model therefore learns patterns from worker behaviour rather than
simply applying a manually defined score at prediction time.

The baseline synthetic formula and the trained ML model are treated as
separate components.

---

## 21. GigScore Conversion

Once the trained model produces a reliability prediction:

\[
\hat{L} = f(X)
\]

the product score is:

\[
\boxed{
GigScore = round(1000 \times \hat{L})
}
\]

Example:

\[
\hat{L}=0.782
\]

therefore:

\[
GigScore=782
\]

GigScore is a prototype supplementary behavioural signal and is not an
official credit score or a directly calibrated probability of loan
repayment.


---

## 22. Feature Normalisation

The raw features have different scales and units. Before they are used in
the synthetic target generator or machine learning pipeline, appropriate
features are normalised to comparable ranges.

### 22.1 Tenure

Tenure is capped at 60 months:

\[
T = \min\left(\frac{tenure\_months}{60}, 1\right)
\]

Examples:

- 6 months → 0.10
- 30 months → 0.50
- 60+ months → 1.00

This prevents extremely long tenure from dominating the score.

---

### 22.2 Rating

The platform rating is normalised from its 0–5 scale:

\[
R = \frac{avg\_rating}{5}
\]

Example:

\[
4.8/5 = 0.96
\]

---

### 22.3 Completion Rate

Completion rate is already represented between 0 and 1:

\[
C = completion\_rate
\]

Example:

\[
95\% = 0.95
\]

---

### 22.4 Cancellation Reliability

Because cancellation is a negative signal, it is inverted:

\[
K = 1 - cancellation\_rate
\]

Example:

\[
3\% \text{ cancellation} \rightarrow K=0.97
\]

Higher values therefore represent stronger completion behaviour.

---

### 22.5 Jobs Completed

Lifetime jobs completed can vary substantially between workers.

For the synthetic target generator, the feature is transformed using
a capped logarithmic scaling:

\[
J_n =
\frac{\log(1+jobs\_completed)}
{\log(1+J_{max})}
\]

where \(J_{max}\) is the chosen upper reference value for the dataset.

This reduces the influence of very large job counts.

---

### 22.6 Income Mean

Income mean is retained as a contextual financial feature.

Because raw income is highly dependent on occupation, platform and location,
the ML pipeline will scale it during preprocessing rather than treating a
larger absolute income as automatically better.

Higher income is therefore not directly interpreted as higher reliability.

---

### 22.7 Income Volatility

Income volatility is measured using the coefficient of variation:

\[
V = \frac{\sigma_{income}}{\mu_{income}}
\]

For model use, volatility is transformed into a bounded stability measure:

\[
V_n =
\frac{1}{1+V}
\]

Higher values indicate greater earnings stability.

---

### 22.8 Income Consistency

Income consistency is defined as:

\[
IC =
\frac{1}{1+income\_volatility}
\]

This is a higher-is-better measure.

---

### 22.9 Income Trend

The raw regression slope depends on income scale, so it is normalised
relative to the worker's mean income:

\[
IT_r =
\frac{slope(month,income)}
{income\_mean}
\]

The resulting value is then bounded to a practical range for the
synthetic-data generator.

Positive values indicate an upward trend.

Negative values indicate a downward trend.

---

### 22.10 Recent Income Change

Recent income change is calculated as:

\[
RIC =
\frac{recent\_income-early\_income}
{early\_income}
\]

This is then bounded during preprocessing to reduce the impact of
extreme observations.

Positive values indicate recent improvement.

Negative values indicate recent deterioration.

---

### 22.11 Work-Volume Trend

The slope of monthly completed jobs is calculated across the 12-month
history and normalised relative to average monthly job volume:

\[
WT_r =
\frac{slope(month,jobs)}
{mean(jobs)}
\]

Positive values indicate increasing work volume.

Negative values indicate decreasing work volume.

---

## 23. Normalisation Principles

Normalisation does not mean that a larger value is always better.

The direction of each feature must be considered.

Examples:

- Higher tenure → generally positive
- Higher completion → positive
- Higher rating → positive
- Higher cancellation → negative
- Higher income volatility → negative
- Positive income trend → generally positive

The final ML pipeline will perform any additional scaling required by the
chosen model using training data only, with the same transformation applied
to unseen data.