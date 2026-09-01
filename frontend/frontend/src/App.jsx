import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [result, setResult] = useState(null);
  const [worker, setWorker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generateRandomWorker() {
    setLoading(true);
    setError("");

    try {
      // Ask our backend for the health of the API first.
      const healthResponse = await fetch(`${API_URL}/health`);

      if (!healthResponse.ok) {
        throw new Error("GigScore backend is not responding.");
      }

      // For now we use one of the synthetic workers generated
      // in our project. Later, this will become a true backend
      // random-worker endpoint.
      const syntheticWorker = createRandomDemoWorker();

      const response = await fetch(`${API_URL}/score`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(syntheticWorker),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Could not calculate GigScore.");
      }

      const data = await response.json();

      setWorker(syntheticWorker);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(
        err.message ||
          "Something went wrong while contacting the GigScore API."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">G</div>

          <div>
            <div className="brand-name">GigScore</div>
            <div className="brand-subtitle">
              Behavioural intelligence for gig workers
            </div>
          </div>
        </div>

        <div className="topbar-right">
          <span className="status-dot" />
          <span>System operational</span>
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <p className="eyebrow">LENDER VIEW</p>

            <h1>
              Understand the worker,
              <br />
              not just the paperwork.
            </h1>

            <p className="hero-copy">
              GigScore converts observable gig-work behaviour into an
              explainable supplementary reliability signal.
            </p>
          </div>

          <button
            className="primary-button"
            onClick={generateRandomWorker}
            disabled={loading}
          >
            {loading ? "Calculating..." : "Generate Random Worker"}
          </button>
        </section>

        {error && (
          <div className="error-box">
            <strong>Backend connection error</strong>
            <span>{error}</span>
            <small>
              Make sure FastAPI is running on
              {" "}
              <code>127.0.0.1:8000</code>.
            </small>
          </div>
        )}

        {!result && !loading && !error && (
          <section className="empty-state">
            <div className="empty-icon">G</div>

            <h2>Ready to score a worker</h2>

            <p>
              Generate a synthetic gig-worker profile and send it through
              the live GigScore ML pipeline.
            </p>

            <button
              className="secondary-button"
              onClick={generateRandomWorker}
            >
              Run first assessment
            </button>
          </section>
        )}

        {loading && (
          <section className="loading-state">
            <div className="loader" />

            <h2>Calculating GigScore...</h2>

            <p>
              Sending the worker profile through feature engineering
              and the trained ML model.
            </p>
          </section>
        )}

        {result && worker && (
          <>
            <section className="profile-row">
              <div className="profile-card">
                <div className="profile-avatar">
                  {worker.worker_id.slice(-2)}
                </div>

                <div>
                  <div className="profile-label">APPLICANT</div>

                  <div className="profile-name">
                    {worker.worker_id}
                  </div>

                  <div className="profile-meta">
                    {worker.platform} · {worker.tenure_months} months
                  </div>
                </div>
              </div>

              <div className="evidence-card">
                <div className="profile-label">
                  EVIDENCE LEVEL
                </div>

                <div className="evidence-value">
                  {result.evidence_level}
                </div>
              </div>
            </section>

            <section className="score-layout">
              <div className="score-card">
                <div className="profile-label">
                  GIGSCORE
                </div>

                <div className="score-number">
                  {result.score}
                </div>

                <div className="score-denominator">
                  / 1000
                </div>

                <div className="tier-badge">
                  {result.tier}
                </div>

                <p className="score-description">
                  {result.summary}
                </p>
              </div>

              <div className="metrics-grid">
                <Metric
                  label="Platform rating"
                  value={worker.avg_rating.toFixed(2)}
                  suffix="/ 5"
                />

                <Metric
                  label="Completion rate"
                  value={`${Math.round(
                    worker.completion_rate * 100
                  )}%`}
                />

                <Metric
                  label="Cancellation rate"
                  value={`${Math.round(
                    worker.cancellation_rate * 100
                  )}%`}
                />

                <Metric
                  label="Lifetime jobs"
                  value={worker.jobs_completed.toLocaleString()}
                />

                <Metric
                  label="Average income"
                  value={formatCurrency(
                    average(worker.monthly_income)
                  )}
                />

                <Metric
                  label="Average monthly jobs"
                  value={Math.round(
                    average(worker.monthly_jobs)
                  )}
                />
              </div>
            </section>

            <section className="explanation-card">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">MODEL EXPLANATION</p>

                  <h2>Why this score?</h2>
                </div>

                <span className="explanation-note">
                  Relative model contribution
                </span>
              </div>

              <div className="factor-columns">
                <FactorColumn
                  title="Positive contributors"
                  positive
                  factors={result.positive_factors}
                />

                <FactorColumn
                  title="Areas requiring attention"
                  factors={result.risk_factors}
                />
              </div>
            </section>

            <section className="disclaimer">
              <strong>Prototype notice</strong>

              <span>
                GigScore is a synthetic-data prototype and supplementary
                behavioural signal. It is not an official credit score
                and does not automatically approve or reject loans.
              </span>
            </section>
          </>
        )}
      </main>
    </div>
  );
}


/* ============================================================
   Metric card
   ============================================================ */

function Metric({ label, value, suffix = "" }) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}
        {suffix && (
          <span className="metric-suffix">
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}


/* ============================================================
   Explanation factor column
   ============================================================ */

function FactorColumn({
  title,
  factors,
  positive = false,
}) {
  return (
    <div className="factor-column">
      <div
        className={
          positive
            ? "factor-title positive"
            : "factor-title"
        }
      >
        <span className="factor-symbol">
          {positive ? "+" : "−"}
        </span>

        {title}
      </div>

      {factors && factors.length > 0 ? (
        <div className="factor-list">
          {factors.map((factor, index) => (
            <div
              className="factor"
              key={`${factor.feature}-${index}`}
            >
              <div className="factor-main">
                <span className="factor-text">
                  {factor.explanation}
                </span>

                <span
                  className={
                    positive
                      ? "factor-impact positive"
                      : "factor-impact negative"
                  }
                >
                  {factor.impact > 0 ? "+" : ""}
                  {factor.impact}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-factors">
          None significant.
        </div>
      )}
    </div>
  );
}


/* ============================================================
   Synthetic demo worker generator
   ============================================================ */

function createRandomDemoWorker() {
  const platforms = [
    "Delivery",
    "Ride-Hailing",
    "Home Services",
    "Freelance",
  ];

  const platform =
    platforms[
      Math.floor(
        Math.random() * platforms.length
      )
    ];

  const tenure =
    Math.floor(
      Math.random() * 49
    ) + 12;

  const rating = clamp(
    3.5 + Math.random() * 1.5,
    3.5,
    5.0
  );

  const completion = clamp(
    0.50 + Math.random() * 0.49,
    0.50,
    0.99
  );

  const cancellation = clamp(
    Math.random() * 0.30,
    0.0,
    0.35
  );

  const jobsBase =
    Math.floor(
      25 + Math.random() * 90
    );

  const monthlyJobs = Array.from(
    { length: 12 },
    () => {
      const variation =
        0.85 +
        Math.random() * 0.30;

      return Math.max(
        1,
        Math.round(
          jobsBase * variation
        )
      );
    }
  );

  const incomeBase =
    9000 +
    Math.random() * 36000;

  const monthlyIncome = Array.from(
    { length: 12 },
    (_, index) => {
      const trend =
        1 +
        ((index - 5.5) *
          (Math.random() * 0.015 - 0.0075));

      const noise =
        0.88 +
        Math.random() * 0.24;

      return Math.max(
        5000,
        Math.round(
          incomeBase *
            trend *
            noise
        )
      );
    }
  );

  const jobsCompleted = Math.max(
    50,
    Math.round(
      tenure *
        jobsBase *
        (0.90 + Math.random() * 0.20)
    )
  );

  return {
    worker_id:
      `DEMO-${Math.floor(
        1000 +
        Math.random() * 9000
      )}`,

    platform,

    tenure_months: tenure,

    avg_rating:
      Number(rating.toFixed(2)),

    completion_rate:
      Number(completion.toFixed(3)),

    cancellation_rate:
      Number(cancellation.toFixed(3)),

    jobs_completed:
      jobsCompleted,

    monthly_income:
      monthlyIncome,

    monthly_jobs:
      monthlyJobs,
  };
}


/* ============================================================
   Utilities
   ============================================================ */

function average(values) {
  return (
    values.reduce(
      (sum, value) =>
        sum + value,
      0
    ) / values.length
  );
}


function formatCurrency(value) {
  return `₹${Math.round(value).toLocaleString(
    "en-IN"
  )}`;
}


function clamp(
  value,
  min,
  max
) {
  return Math.min(
    Math.max(value, min),
    max
  );
}


export default App;