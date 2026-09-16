import { useEffect, useState } from "react";
import { fetchDailyReport } from "../api.js";

export default function Reports() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDailyReport()
      .then(setReport)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <p className="muted">Loading daily summary…</p>;

  return (
    <div>
      <h2>Daily production summary</h2>
      <section className="card">
        <pre className="advice">{report.text}</pre>
      </section>
    </div>
  );
}
