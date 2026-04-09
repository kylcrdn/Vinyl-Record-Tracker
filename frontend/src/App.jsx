import { useState } from "react";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [record, setRecord] = useState(null);
  const [resultCount, setResultCount] = useState(null);
  const [status, setStatus] = useState(
    "Search by artist, title, or Discogs ID.",
  );
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setStatus("Enter an artist name, album title, or Discogs ID first.");
      setRecord(null);
      setResultCount(null);
      return;
    }

    const params = new URLSearchParams({ query: trimmedQuery });

    setIsLoading(true);
    setStatus("Searching Discogs...");
    setRecord(null);

    try {
      const response = await fetch(`/records/search?${params.toString()}`);
      const data = await response.json();

      if (!response.ok) {
        setStatus(data.detail || "Request failed.");
        setResultCount(null);
        return;
      }

      if (!data.results?.length) {
        setStatus("No vinyl records found for that search.");
        setResultCount(0);
        return;
      }

      setRecord(data.results[0]);
      setResultCount(data.results.length);
      setStatus(`Showing the top match from ${data.results.length} result(s).`);
    } catch {
      setStatus("Request failed. Check that the backend is running.");
      setResultCount(null);
    } finally {
      setIsLoading(false);
    }
  }

  const metaItems = [];
  if (record?.year) metaItems.push(record.year);
  if (Array.isArray(record?.formats))
    metaItems.push(...record.formats.slice(0, 3));

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <p className="eyebrow">React frontend + FastAPI backend</p>
        <h1>Vinyl Record Tracker</h1>
        <p className="hero-copy">
          Search Discogs from a React UI now, then extend this into your saved
          collection once the backend CRUD layer is ready.
        </p>

        <form className="search-form" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="query">
            Search by artist, title, or Discogs ID
          </label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by artist, title, or Discogs ID"
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        <p className="status-message">{status}</p>

        <div className="stat-row">
          <div className="stat-card">
            <span className="stat-label">Backend route</span>
            <strong>/records/search</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Results</span>
            <strong>{resultCount ?? "—"}</strong>
          </div>
        </div>
      </section>

      <section className={`record-card${record ? " visible" : ""}`}>
        {record ? (
          <>
            <div className="artwork-frame">
              {record.cover_image ? (
                <img
                  src={record.cover_image}
                  alt={record.title || "Vinyl cover art"}
                />
              ) : (
                <div className="artwork-fallback">LP</div>
              )}
            </div>

            <div className="record-content">
              <p className="card-label">Top Match</p>
              <h2>{record.title || "Untitled release"}</h2>
              <p className="card-subtitle">{formatLabels(record.labels)}</p>

              <div className="meta-row">
                {metaItems.map((item) => (
                  <span key={item} className="meta-pill">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <p className="card-label">No result selected</p>
            <h2>Your top match will appear here</h2>
            <p className="card-subtitle">
              Start with an artist, album title, or exact Discogs release ID.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}

function formatLabels(labels) {
  if (!Array.isArray(labels) || !labels.length) {
    return "Label unknown";
  }

  return labels.slice(0, 2).join(" • ");
}

export default App;
