import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "https://gigscore-xogt.onrender.com";

function App() {
  const [view, setView] = useState("home");

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  const [worker, setWorker] = useState(null);
  const [result, setResult] = useState(null);

  const [searching, setSearching] = useState(false);
  const [loadingScore, setLoadingScore] = useState(false);

  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const [showDropdown, setShowDropdown] = useState(false);

  const searchRef = useRef(null);

  // ============================================================
  // SWITCH VIEW
  // ============================================================

  function switchView(newView) {
    setView(newView);
  }

  // ============================================================
  // LIVE LENDER SEARCH
  // ============================================================

  useEffect(() => {
    if (view !== "lender") {
      return;
    }

    const query = searchQuery.trim();

    if (!query) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setSearching(true);

        const response = await fetch(
          `${API_URL}/search?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
          throw new Error("Could not search workers.");
        }

        const data = await response.json();

        setSearchResults(data.workers || []);
        setShowDropdown(true);
      } catch (err) {
        console.error(err);

        setSearchResults([]);
        setShowDropdown(false);
      } finally {
        setSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery, view]);

  // ============================================================
  // CLOSE SEARCH DROPDOWN
  // ============================================================

  useEffect(() => {
    function handleOutsideClick(event) {
      if (
        searchRef.current &&
        !searchRef.current.contains(event.target)
      ) {
        setShowDropdown(false);
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      );
    };
  }, []);

  // ============================================================
  // LENDER SEARCH
  // ============================================================

  async function searchWorkers(event) {
    if (event) {
      event.preventDefault();
    }

    const query = searchQuery.trim();

    if (!query) {
      setError(
        "Enter a worker name, phone number, or worker ID."
      );
      return;
    }

    setSearching(true);
    setError("");
    setSearched(true);
    setShowDropdown(false);
    setWorker(null);
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        throw new Error("Could not search workers.");
      }

      const data = await response.json();
      const workers = data.workers || [];

      setSearchResults(workers);

      if (workers.length === 0) {
        setError(
          "No worker found matching your search."
        );
      } else if (workers.length === 1) {
        await selectWorker(workers[0].worker_id);
      }
    } catch (err) {
      console.error(err);

      setSearchResults([]);

      setError(
        err.message ||
          "Unable to connect to the GigScore backend."
      );
    } finally {
      setSearching(false);
    }
  }

  // ============================================================
  // LOAD WORKER PROFILE + SCORE
  // ============================================================

  async function selectWorker(workerId) {
    setShowDropdown(false);
    setLoadingScore(true);
    setError("");
    setResult(null);

    try {
      const workerResponse = await fetch(
        `${API_URL}/worker/${encodeURIComponent(workerId)}`
      );

      if (!workerResponse.ok) {
        throw new Error(
          "Could not load worker profile."
        );
      }

      const workerData =
        await workerResponse.json();

      setWorker(workerData);

      const scoreResponse = await fetch(
        `${API_URL}/score`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(workerData),
        }
      );

      if (!scoreResponse.ok) {
        const message =
          await scoreResponse.text();

        throw new Error(
          message ||
            "Could not calculate GigScore."
        );
      }

      const scoreData =
        await scoreResponse.json();

      setResult(scoreData);

      setSearchQuery(
        workerData.name || workerData.phone || workerId
      );
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Something went wrong while loading this worker."
      );
    } finally {
      setLoadingScore(false);
    }
  }

  // ============================================================
  // CLEAR LENDER SEARCH
  // ============================================================

  function clearSearch() {
    setSearchQuery("");
    setSearchResults([]);
    setWorker(null);
    setResult(null);
    setError("");
    setSearched(false);
    setShowDropdown(false);
  }

  // ============================================================
  // INITIALS
  // ============================================================

  function getInitials(name) {
    if (!name) {
      return "GW";
    }

    return name
      .split(" ")
      .filter(Boolean)
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }

  // ============================================================
  // MAIN APP
  // ============================================================

  return (
    <div className="app">

      {/* ======================================================
          TOP BAR
      ====================================================== */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            G
          </div>

          <div>
            <div className="brand-name">
              GigScore
            </div>

            <div className="brand-subtitle">
              Behavioural intelligence for gig workers
            </div>
          </div>

        </div>

        <div className="view-switcher">

          <button
            className={
              view === "home"
                ? "view-button active"
                : "view-button"
            }
            onClick={() =>
              switchView("home")
            }
          >
            Home
          </button>

          <button
            className={
              view === "lender"
                ? "view-button active"
                : "view-button"
            }
            onClick={() =>
              switchView("lender")
            }
          >
            Lender View
          </button>

          <button
            className={
              view === "worker"
                ? "view-button active"
                : "view-button"
            }
            onClick={() =>
              switchView("worker")
            }
          >
            Worker View
          </button>

        </div>

        <div className="topbar-right">

          <span className="status-dot" />

          <span>
            System operational
          </span>

        </div>

      </header>



      {/* ======================================================
          HOME VIEW
      ====================================================== */}

      {view === "home" && (

        <HomeView
          onLender={() =>
            switchView("lender")
          }
          onWorker={() =>
            switchView("worker")
          }
        />

      )}



      {/* ======================================================
          LENDER VIEW
      ====================================================== */}

      {view === "lender" && (

        <main className="dashboard">

          <section className="hero">

            <div className="hero-copy-block">

              <p className="eyebrow">
                LENDER VIEW
              </p>

              <h1>
                Understand the worker,
                <br />
                not just the paperwork.
              </h1>

              <p className="hero-copy">
                GigScore converts observable gig-work
                behaviour into an explainable
                supplementary reliability signal.
              </p>

            </div>



            <form
              className="search-form"
              onSubmit={searchWorkers}
            >

              <div
                className="search-input-wrap"
                ref={searchRef}
              >

                <span className="search-icon">
                  ⌕
                </span>

                <input
                  type="text"
                  value={searchQuery}
                  onChange={(event) => {
                    setSearchQuery(
                      event.target.value
                    );

                    setError("");
                    setSearched(false);
                  }}
                  onFocus={() => {
                    if (
                      searchResults.length > 0
                    ) {
                      setShowDropdown(true);
                    }
                  }}
                  placeholder="Search worker by name or phone number"
                  aria-label="Search worker"
                  autoComplete="off"
                />

                {searchQuery && (

                  <button
                    type="button"
                    className="clear-search"
                    onClick={clearSearch}
                  >
                    ×
                  </button>

                )}



                {showDropdown &&
                  searchQuery.trim() && (

                    <div className="search-dropdown">

                      {searching && (
                        <div className="dropdown-status">
                          Searching workers...
                        </div>
                      )}

                      {!searching &&
                        searchResults.length === 0 && (
                          <div className="dropdown-status">
                            No workers found
                          </div>
                        )}

                      {!searching &&
                        searchResults.length > 0 && (

                          <>
                            <div className="dropdown-heading">
                              WORKERS
                            </div>

                            {searchResults.map(
                              (candidate) => (

                                <button
                                  type="button"
                                  className="dropdown-worker"
                                  key={
                                    candidate.worker_id
                                  }
                                  onClick={() =>
                                    selectWorker(
                                      candidate.worker_id
                                    )
                                  }
                                >

                                  <div className="dropdown-avatar">
                                    {getInitials(
                                      candidate.name
                                    )}
                                  </div>

                                  <div className="dropdown-details">

                                    <strong>
                                      {candidate.name}
                                    </strong>

                                    <span>
                                      {candidate.phone}
                                    </span>

                                    <small>
                                      {candidate.worker_id}
                                      {" · "}
                                      {candidate.platform}
                                    </small>

                                  </div>

                                  <div className="dropdown-arrow">
                                    →
                                  </div>

                                </button>

                              )
                            )}

                          </>

                        )}

                    </div>

                  )}

              </div>



              <button
                className="primary-button"
                type="submit"
                disabled={searching}
              >
                {searching
                  ? "Searching..."
                  : "Search"}
              </button>

            </form>

          </section>



          {/* ERROR */}

          {error && (

            <div className="error-box">

              <div className="error-icon">
                !
              </div>

              <div>

                <strong>
                  {error.includes("backend")
                    ? "Backend connection error"
                    : "Search notice"}
                </strong>

                <span>
                  {error}
                </span>

                {error.includes("backend") && (
                  <small>
                    Make sure FastAPI is running on{" "}
                    <code>
                      127.0.0.1:8000
                    </code>
                    .
                  </small>
                )}

              </div>

            </div>

          )}



          {/* SEARCH RESULTS */}

          {searchResults.length > 0 &&
            !worker &&
            searched && (

              <section className="search-results-card">

                <div className="section-heading compact">

                  <div>

                    <p className="eyebrow">
                      SEARCH RESULTS
                    </p>

                    <h2>
                      {searchResults.length} worker
                      {searchResults.length !== 1
                        ? "s"
                        : ""}{" "}
                      found
                    </h2>

                  </div>

                  <span className="result-hint">
                    Select a profile to assess
                  </span>

                </div>



                <div className="worker-results">

                  {searchResults.map(
                    (candidate) => (

                      <button
                        className="worker-result"
                        key={
                          candidate.worker_id
                        }
                        onClick={() =>
                          selectWorker(
                            candidate.worker_id
                          )
                        }
                      >

                        <div className="result-avatar">
                          {getInitials(
                            candidate.name
                          )}
                        </div>

                        <div className="result-details">

                          <strong>
                            {candidate.name}
                          </strong>

                          <span>
                            {candidate.phone}
                          </span>

                          <small>
                            {candidate.worker_id}
                            {" · "}
                            {candidate.platform}
                            {" · "}
                            {candidate.tenure_months}
                            {" months"}
                          </small>

                        </div>

                        <div className="result-arrow">
                          →
                        </div>

                      </button>

                    )
                  )}

                </div>

              </section>

            )}



          {/* EMPTY STATE */}

          {!searched &&
            !worker &&
            !loadingScore && (

              <section className="empty-state">

                <div className="empty-icon">
                  G
                </div>

                <h2>
                  Search for a worker
                </h2>

                <p>
                  Find a gig worker using their
                  name, phone number, or worker ID
                  to view their behavioural
                  reliability profile.
                </p>

                <div className="search-examples">

                  <span>NAME</span>
                  <span>PHONE</span>
                  <span>WORKER ID</span>

                </div>

              </section>

            )}



          {/* LOADING */}

          {loadingScore && (

            <section className="loading-state">

              <div className="loader" />

              <h2>
                Calculating GigScore...
              </h2>

              <p>
                Retrieving the worker profile and
                running the behavioural scoring
                pipeline.
              </p>

            </section>

          )}



          {/* PROFILE */}

          {worker &&
            result &&
            !loadingScore && (

              <LenderProfile
                worker={worker}
                result={result}
                getInitials={getInitials}
                clearSearch={clearSearch}
              />

            )}

        </main>

      )}



      {/* ======================================================
          WORKER VIEW
      ====================================================== */}

      <div
        style={{
          display: view === "worker"
            ? "block"
            : "none",
        }}
      >

        <WorkerView
          getInitials={getInitials}
          onLoadWorker={selectWorker}
          active={view === "worker"}
          worker={worker}
          result={result}
          loadingScore={loadingScore}
          error={error}
          setError={setError}
          clearWorker={() => {
            setWorker(null);
            setResult(null);
            setError("");
          }}
        />

      </div>

    </div>
  );
}



// ============================================================
// HOME VIEW
// ============================================================

function HomeView({
  onLender,
  onWorker,
}) {

  return (

    <main className="home-dashboard">

      <section className="home-hero">

        <div className="home-hero-copy">

          <p className="eyebrow">
            GIGSCORE
          </p>

          <h1>
            Behavioural intelligence
            <br />
            for the gig economy.
          </h1>

          <p>
            GigScore converts observable gig-work
            behaviour into an explainable
            supplementary reliability signal.
          </p>

        </div>

      </section>



      <section className="home-role-section">

        <div className="section-heading">

          <div>

            <p className="eyebrow">
              CHOOSE YOUR VIEW
            </p>

            <h2>
              What would you like to do?
            </h2>

          </div>

        </div>



        <div className="home-role-grid">

          <button
            className="home-role-card"
            onClick={onLender}
          >

            <div className="home-role-icon">
              L
            </div>

            <div className="home-role-copy">

              <p className="eyebrow">
                FOR LENDERS
              </p>

              <h3>
                Assess a worker
              </h3>

              <p>
                Search for a gig worker and
                understand their behavioural
                reliability profile.
              </p>

            </div>

            <span className="home-role-arrow">
              →
            </span>

          </button>



          <button
            className="home-role-card"
            onClick={onWorker}
          >

            <div className="home-role-icon">
              G
            </div>

            <div className="home-role-copy">

              <p className="eyebrow">
                FOR GIG WORKERS
              </p>

              <h3>
                View your GigScore
              </h3>

              <p>
                Explore your work history,
                understand your score, and see
                what influences your profile.
              </p>

            </div>

            <span className="home-role-arrow">
              →
            </span>

          </button>

        </div>

      </section>



      <section className="home-value-strip">

        <div className="home-value-item">

          <strong>
            Behaviour-based
          </strong>

          <span>
            Observable work signals
          </span>

        </div>



        <div className="home-value-item">

          <strong>
            Explainable
          </strong>

          <span>
            Understand what drives the score
          </span>

        </div>



        <div className="home-value-item">

          <strong>
            Supplementary
          </strong>

          <span>
            Additional context beyond paperwork
          </span>

        </div>



        <div className="home-value-item">

          <strong>
            Worker-controlled
          </strong>

          <span>
            Workers decide profile access
          </span>

        </div>

      </section>



      <section className="disclaimer">

        <strong>
          Prototype notice
        </strong>

        <span>
          GigScore is a synthetic-data prototype
          and supplementary behavioural signal.
          It is not an official credit score and
          does not automatically approve or reject
          loans.
        </span>

      </section>

    </main>

  );
}



// ============================================================
// LENDER PROFILE
// ============================================================

function LenderProfile({
  worker,
  result,
  getInitials,
  clearSearch,
}) {

  return (

    <>

      <section className="profile-row">

        <div className="profile-card">

          <div className="profile-avatar">
            {getInitials(worker.name)}
          </div>

          <div className="profile-information">

            <div className="profile-label">
              APPLICANT
            </div>

            <div className="profile-name">
              {worker.name}
            </div>

            <div className="profile-phone">
              {worker.phone}
            </div>

            <div className="profile-meta">
              {worker.platform}
              {" · "}
              {worker.tenure_months}
              {" months"}
              {" · "}
              {worker.worker_id}
            </div>

          </div>

          <button
            className="change-worker-button"
            onClick={clearSearch}
          >
            Change worker
          </button>

        </div>



        <div className="evidence-card">

          <div className="profile-label">
            EVIDENCE LEVEL
          </div>

          <div className="evidence-value">
            {result.evidence_level}
          </div>

          <div className="evidence-subtitle">
            Based on observed work history
          </div>

        </div>

      </section>



      <section className="score-layout">

        <ScoreCard result={result} />

        <MetricsGrid worker={worker} />

      </section>



      <Explanation result={result} />



      <section className="disclaimer">

        <strong>
          Prototype notice
        </strong>

        <span>
          GigScore is a synthetic-data prototype
          and supplementary behavioural signal.
          It is not an official credit score and
          does not automatically approve or reject
          loans.
        </span>

      </section>

    </>

  );
}



// ============================================================
// WORKER VIEW
// ============================================================

function WorkerView({
  getInitials,
  onLoadWorker,
  active,
  worker,
  result,
  loadingScore,
  error,
  setError,
  clearWorker,
}) {

  const [workerQuery, setWorkerQuery] = useState("");
  const [workerSearchResults, setWorkerSearchResults] =
    useState([]);

  const [workerSearching, setWorkerSearching] =
    useState(false);

  const [showWorkerResults, setShowWorkerResults] =
    useState(false);

  const [lenderAuthorized, setLenderAuthorized] =
    useState(false);

  const workerSearchRef = useRef(null);



  // ==========================================================
  // WORKER LIVE SEARCH
  // ==========================================================

  useEffect(() => {

    if (worker || !active) {
      return;
    }

    const query = workerQuery.trim();

    if (!query) {
      setWorkerSearchResults([]);
      setShowWorkerResults(false);
      return;
    }

    const timer = setTimeout(async () => {

      try {

        setWorkerSearching(true);

        const response = await fetch(
          `${API_URL}/search?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
          throw new Error(
            "Could not search workers."
          );
        }

        const data =
          await response.json();

        setWorkerSearchResults(
          data.workers || []
        );

        setShowWorkerResults(true);

      } catch (err) {

        console.error(err);

        setWorkerSearchResults([]);
        setShowWorkerResults(false);

      } finally {

        setWorkerSearching(false);

      }

    }, 250);

    return () => clearTimeout(timer);

  }, [workerQuery, worker, active]);



  // ==========================================================
  // CLOSE WORKER SEARCH
  // ==========================================================

  useEffect(() => {

    function handleOutsideClick(event) {

      if (
        workerSearchRef.current &&
        !workerSearchRef.current.contains(
          event.target
        )
      ) {

        setShowWorkerResults(false);

      }

    }

    document.addEventListener(
      "mousedown",
      handleOutsideClick
    );

    return () => {

      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      );

    };

  }, []);



  // ==========================================================
  // WORKER SEARCH
  // ==========================================================

  async function handleWorkerSearch(event) {

    event.preventDefault();

    const query =
      workerQuery.trim();

    if (!query) {

      setError(
        "Enter your name, phone number, or Worker ID."
      );

      return;

    }

    setError("");
    setWorkerSearching(true);
    setShowWorkerResults(false);

    try {

      const response = await fetch(
        `${API_URL}/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {

        throw new Error(
          "Could not search workers."
        );

      }

      const data =
        await response.json();

      const workers =
        data.workers || [];

      setWorkerSearchResults(
        workers
      );

      if (workers.length === 0) {

        setError(
          "No worker profile found matching your search."
        );

      } else if (workers.length === 1) {

        setWorkerQuery(
          workers[0].name ||
          workers[0].phone ||
          workers[0].worker_id
        );

        await onLoadWorker(
          workers[0].worker_id
        );

      } else {

        setShowWorkerResults(true);

      }

    } catch (err) {

      console.error(err);

      setError(
        err.message ||
          "Unable to connect to the GigScore backend."
      );

    } finally {

      setWorkerSearching(false);

    }

  }



  // ==========================================================
  // SELECT WORKER FROM SEARCH
  // ==========================================================

  async function selectWorkerFromSearch(
    workerId
  ) {

    setShowWorkerResults(false);
    setError("");

    await onLoadWorker(workerId);

  }



  // ==========================================================
  // LOADING SCREEN
  // ==========================================================

  if (loadingScore && active) {

    return (

      <main className="worker-dashboard">

        <section className="worker-loading">

          <div className="worker-loading-orb">
            G
          </div>

          <div className="loader" />

          <p className="eyebrow">
            WORKER PROFILE
          </p>

          <h1>
            Building your
            <br />
            GigScore profile.
          </h1>

          <p>
            Retrieving your work history
            and calculating your behavioural
            reliability signal.
          </p>

        </section>

      </main>

    );

  }



  // ==========================================================
  // WORKER LOGIN / SEARCH
  // ==========================================================

  if (!worker || !result) {

    return (

      <main className="worker-dashboard">

        <section className="worker-hero">

          <div className="worker-hero-copy">

            <div className="worker-kicker">
              FOR GIG WORKERS
            </div>

            <h1>
              Your work.
              <br />
              <span>Your signal.</span>
            </h1>

            <p>
              GigScore helps you understand how
              your observable work behaviour is
              represented as a reliability signal.
            </p>

            <div className="worker-trust-row">

              <div>
                <span className="trust-icon">
                  ✓
                </span>
                Explainable
              </div>

              <div>
                <span className="trust-icon">
                  ✓
                </span>
                Behaviour-based
              </div>

              <div>
                <span className="trust-icon">
                  ✓
                </span>
                Worker-controlled
              </div>

            </div>

          </div>



          <form
            className="worker-access-card"
            onSubmit={handleWorkerSearch}
          >

            <div className="worker-access-icon">
              G
            </div>

            <p className="eyebrow">
              ACCESS YOUR PROFILE
            </p>

            <h2>
              Find your profile
            </h2>

            <p className="worker-access-copy">
              Search using your name, phone number,
              or GigScore Worker ID.
            </p>



            <label>
              NAME / PHONE / WORKER ID
            </label>



            <div
              className="worker-search-wrap"
              ref={workerSearchRef}
            >

              <span className="worker-search-icon">
                ⌕
              </span>

              <input
                type="text"
                value={workerQuery}
                onChange={(event) => {

                  setWorkerQuery(
                    event.target.value
                  );

                  setError("");

                }}
                onFocus={() => {

                  if (
                    workerSearchResults.length > 0
                  ) {

                    setShowWorkerResults(true);

                  }

                }}
                placeholder="Name, phone number or W00014"
                autoComplete="off"
              />



              {workerSearching && (

                <span className="worker-search-spinner">
                  ...
                </span>

              )}



              {showWorkerResults &&
                workerSearchResults.length > 0 && (

                  <div className="worker-search-dropdown">

                    <div className="dropdown-heading">
                      MATCHING PROFILES
                    </div>

                    {workerSearchResults.map(
                      (candidate) => (

                        <button
                          type="button"
                          className="dropdown-worker"
                          key={
                            candidate.worker_id
                          }
                          onClick={() =>
                            selectWorkerFromSearch(
                              candidate.worker_id
                            )
                          }
                        >

                          <div className="dropdown-avatar">
                            {getInitials(
                              candidate.name
                            )}
                          </div>

                          <div className="dropdown-details">

                            <strong>
                              {candidate.name}
                            </strong>

                            <span>
                              {candidate.phone}
                            </span>

                            <small>
                              {candidate.worker_id}
                              {" · "}
                              {candidate.platform}
                            </small>

                          </div>

                          <div className="dropdown-arrow">
                            →
                          </div>

                        </button>

                      )
                    )}

                  </div>

                )}

            </div>



            {error && (

              <div className="worker-error">
                {error}
              </div>

            )}



            <button
              className="worker-primary-button"
              type="submit"
              disabled={workerSearching}
            >

              {workerSearching
                ? "Searching..."
                : "View my GigScore"}

              <span>
                →
              </span>

            </button>



            <small className="worker-access-note">
              Demo access uses profiles from the
              GigScore prototype dataset.
            </small>

          </form>

        </section>



        <section className="worker-feature-grid">

          <div className="worker-feature">

            <div className="feature-number">
              01
            </div>

            <h3>
              Understand your score
            </h3>

            <p>
              See the work behaviours that
              contribute positively or negatively
              to your GigScore.
            </p>

          </div>



          <div className="worker-feature">

            <div className="feature-number">
              02
            </div>

            <h3>
              See your work history
            </h3>

            <p>
              Review your income, completed jobs,
              ratings, completion and cancellation
              patterns.
            </p>

          </div>



          <div className="worker-feature">

            <div className="feature-number">
              03
            </div>

            <h3>
              Improve over time
            </h3>

            <p>
              Understand which areas could make
              your reliability signal stronger.
            </p>

          </div>

        </section>

      </main>

    );

  }



  // ==========================================================
  // WORKER PROFILE
  // ==========================================================

  return (

    <main className="worker-dashboard">



      {/* ======================================================
          PROFILE HEADER
      ====================================================== */}

      <section className="worker-profile-header">

        <div className="worker-identity">

          <div className="worker-large-avatar">
            {getInitials(worker.name)}
          </div>

          <div>

            <p className="eyebrow">
              YOUR GIGSCORE PROFILE
            </p>

            <h1>
              {worker.name}
            </h1>

            {/* PHONE NEXT TO NAME */}

            <p className="worker-phone-line">
              {worker.phone}
            </p>

            <p className="worker-id-line">
              {worker.platform}
              {" · "}
              {worker.worker_id}
            </p>

          </div>

        </div>



        <div className="worker-profile-status">

          <span className="status-dot" />

          Profile active

        </div>

      </section>



      {/* ======================================================
          SCORE HERO
      ====================================================== */}

      <section className="worker-score-hero">

        <div className="worker-score-main">

          <p className="profile-label">
            YOUR GIGSCORE
          </p>

          <div className="worker-score-number">
            {result.score}
            <span>
              / 1000
            </span>
          </div>

          <div className="worker-tier">
            {result.tier}
          </div>

          <p className="worker-score-summary">
            {result.summary}
          </p>

        </div>



        <div className="worker-score-message">

          <div className="message-icon">
            ✦
          </div>

          <div>

            <strong>
              What does this mean?
            </strong>

            <p>
              Your GigScore is a supplementary
              behavioural signal based on your
              observable gig-work history. It gives
              lenders additional context beyond
              traditional paperwork.
            </p>

          </div>

        </div>

      </section>



      {/* ======================================================
          METRICS
      ====================================================== */}

      <section className="worker-section">

        <div className="section-heading">

          <div>

            <p className="eyebrow">
              YOUR WORK PROFILE
            </p>

            <h2>
              The numbers behind your score
            </h2>

          </div>

        </div>

        <MetricsGrid worker={worker} />

      </section>



      {/* ======================================================
          WORK HISTORY
      ====================================================== */}

      <section className="worker-section">

        <div className="section-heading">

          <div>

            <p className="eyebrow">
              WORK HISTORY
            </p>

            <h2>
              Your last 12 months
            </h2>

          </div>

          <span className="explanation-note">
            Observed platform activity
          </span>

        </div>



        <div className="history-grid">

          <HistoryChart
            title="Monthly income"
            values={worker.monthly_income}
            formatter={(value) =>
              formatCurrency(value)
            }
          />

          <HistoryChart
            title="Completed jobs"
            values={worker.monthly_jobs}
            formatter={(value) =>
              Math.round(value).toLocaleString()
            }
          />

        </div>

      </section>



      {/* ======================================================
          MODEL EXPLANATION
      ====================================================== */}

      <section className="worker-section">

        <Explanation result={result} />

      </section>



      {/* ======================================================
          IMPROVEMENT GUIDANCE
      ====================================================== */}

      <section className="improvement-card">

        <div className="improvement-icon">
          ↗
        </div>

        <div className="improvement-copy">

          <p className="eyebrow">
            IMPROVE YOUR GIGSCORE
          </p>

          <h2>
            Build a stronger reliability profile.
          </h2>

          <p>
            Your GigScore reflects patterns in your
            observable work behaviour. Focus on the
            areas below to strengthen your profile
            over time.
          </p>



          <div className="improvement-list">

            <div className="improvement-item">

              <span className="improvement-check">
                ✓
              </span>

              <div>

                <strong>
                  Complete more jobs consistently
                </strong>

                <span>
                  Maintaining a strong completion
                  rate shows dependable work behaviour.
                </span>

              </div>

            </div>



            <div className="improvement-item">

              <span className="improvement-check">
                ✓
              </span>

              <div>

                <strong>
                  Reduce cancellations
                </strong>

                <span>
                  Fewer cancellations can strengthen
                  your reliability signal.
                </span>

              </div>

            </div>



            <div className="improvement-item">

              <span className="improvement-check">
                ✓
              </span>

              <div>

                <strong>
                  Maintain strong ratings
                </strong>

                <span>
                  Consistent positive customer ratings
                  contribute to your behavioural profile.
                </span>

              </div>

            </div>



            <div className="improvement-item">

              <span className="improvement-check">
                ✓
              </span>

              <div>

                <strong>
                  Keep working consistently
                </strong>

                <span>
                  A stable work history gives the model
                  more evidence about your reliability.
                </span>

              </div>

            </div>

          </div>

        </div>

      </section>



      {/* ======================================================
          AUTHORIZATION
      ====================================================== */}

      <section className="consent-preview">

        <div className="consent-preview-icon">
          🔐
        </div>

        <div className="consent-preview-copy">

          <p className="eyebrow">
            YOUR DATA, YOUR CONTROL
          </p>

          <h2>
            You decide who sees your profile.
          </h2>

          <p>
            Authorize a lender to access your GigScore
            profile and behavioural reliability information.
            You control whether your profile is shared.
          </p>

        </div>



        <div className="consent-action">

          <div
            className={
              lenderAuthorized
                ? "consent-status authorized"
                : "consent-status"
            }
          >

            <span>

              {lenderAuthorized
                ? "✓ Profile updated to lender"
                : "No lender access"}

            </span>

            <small>

              {lenderAuthorized
                ? "Lender can now access your profile"
                : "Your profile is currently private"}

            </small>

          </div>



          {!lenderAuthorized && (

            <button
              className="authorize-button"
              type="button"
              onClick={() =>
                setLenderAuthorized(true)
              }
            >

              Authorize profile

              <span>
                →
              </span>

            </button>

          )}

        </div>

      </section>



      {/* ======================================================
          SEARCH ANOTHER WORKER
      ====================================================== */}

      <button
        className="worker-reset-button"
        onClick={() => {
          setLenderAuthorized(false);
          setWorkerQuery("");
          setWorkerSearchResults([]);
          clearWorker();
        }}
      >
        ← Search another worker
      </button>



      {/* ======================================================
          DISCLAIMER
      ====================================================== */}

      <section className="disclaimer">

        <strong>
          Prototype notice
        </strong>

        <span>
          GigScore is a synthetic-data prototype
          and supplementary behavioural signal.
          It is not an official credit score and
          does not automatically approve or reject
          loans.
        </span>

      </section>

    </main>

  );
}



// ============================================================
// SCORE CARD
// ============================================================

function ScoreCard({ result }) {

  return (

    <div className="score-card">

      <div className="profile-label">
        GIGSCORE
      </div>

      <div className="score-display">

        <div className="score-number">
          {result.score}
        </div>

        <div className="score-denominator">
          / 1000
        </div>

      </div>

      <div className="tier-badge">
        {result.tier}
      </div>

      <p className="score-description">
        {result.summary}
      </p>

    </div>

  );
}



// ============================================================
// METRICS GRID
// ============================================================

function MetricsGrid({ worker }) {

  return (

    <div className="metrics-grid">

      <Metric
        label="Platform rating"
        value={
          Number(worker.avg_rating).toFixed(2)
        }
        suffix="/ 5"
      />

      <Metric
        label="Completion rate"
        value={
          `${Math.round(
            worker.completion_rate * 100
          )}%`
        }
      />

      <Metric
        label="Cancellation rate"
        value={
          `${Math.round(
            worker.cancellation_rate * 100
          )}%`
        }
      />

      <Metric
        label="Lifetime jobs"
        value={
          Number(
            worker.jobs_completed
          ).toLocaleString()
        }
      />

      <Metric
        label="Average income"
        value={
          formatCurrency(
            average(
              worker.monthly_income
            )
          )
        }
      />

      <Metric
        label="Average monthly jobs"
        value={
          Math.round(
            average(
              worker.monthly_jobs
            )
          )
        }
      />

    </div>

  );
}



// ============================================================
// METRIC
// ============================================================

function Metric({
  label,
  value,
  suffix = "",
}) {

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



// ============================================================
// HISTORY CHART
// ============================================================

function HistoryChart({
  title,
  values,
  formatter,
}) {

  const safeValues =
    Array.isArray(values)
      ? values
      : [];

  const max =
    Math.max(
      ...(safeValues.length
        ? safeValues
        : [1]),
      1
    );

  return (

    <div className="history-card">

      <div className="history-card-header">

        <div>

          <p className="profile-label">
            {title}
          </p>

          <strong>

            {formatter(
              average(safeValues)
            )}

            <span>
              {" "}average
            </span>

          </strong>

        </div>

      </div>



      <div className="history-bars">

        {safeValues.map(
          (value, index) => {

            const height =
              Math.max(
                5,
                (Number(value) / max) * 100
              );

            return (

              <div
                className="history-bar-column"
                key={index}
              >

                <div
                  className="history-bar"
                  style={{
                    height: `${height}%`,
                  }}
                  title={formatter(value)}
                />

                <span>
                  {index + 1}
                </span>

              </div>

            );

          }
        )}

      </div>



      <div className="history-label">
        Month 1 → Month 12
      </div>

    </div>

  );
}



// ============================================================
// EXPLANATION
// ============================================================

function Explanation({ result }) {

  return (

    <section className="explanation-card">

      <div className="section-heading">

        <div>

          <p className="eyebrow">
            MODEL EXPLANATION
          </p>

          <h2>
            Why this score?
          </h2>

        </div>

        <span className="explanation-note">
          Relative model contribution
        </span>

      </div>



      <div className="factor-columns">

        <FactorColumn
          title="Positive contributors"
          positive
          factors={
            result.positive_factors
          }
        />

        <FactorColumn
          title="Areas requiring attention"
          factors={
            result.risk_factors
          }
        />

      </div>

    </section>

  );
}



// ============================================================
// FACTOR COLUMN
// ============================================================

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



      {factors &&
      factors.length > 0 ? (

        <div className="factor-list">

          {factors.map(
            (factor, index) => (

              <div
                className="factor"
                key={
                  `${factor.feature}-${index}`
                }
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

                    {factor.impact > 0
                      ? "+"
                      : ""}

                    {factor.impact}

                  </span>

                </div>

              </div>

            )
          )}

        </div>

      ) : (

        <div className="no-factors">
          None significant.
        </div>

      )}

    </div>

  );
}



// ============================================================
// HELPERS
// ============================================================

function average(values) {

  if (
    !values ||
    values.length === 0
  ) {
    return 0;
  }

  return (
    values.reduce(
      (sum, value) =>
        sum + Number(value || 0),
      0
    ) / values.length
  );

}



function formatCurrency(value) {

  return `₹${Math.round(
    value || 0
  ).toLocaleString("en-IN")}`;

}



export default App;