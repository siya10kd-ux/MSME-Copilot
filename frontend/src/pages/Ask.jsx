import { useState } from "react";
import { askQuestion } from "../api.js";

export default function Ask() {
  const [question, setQuestion] = useState(
    "Which products are profitable but frequently delayed?"
  );
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      setResult(await askQuestion(question));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Business Q&amp;A</h2>
      <form className="card" onSubmit={onSubmit}>
        <textarea
          rows={4}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <p>
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Asking agents…" : "Ask Business Advisor"}
          </button>
        </p>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <section className="card" style={{ marginTop: 16 }}>
          <h3>Answer</h3>
          <p className="advice">{result.final_advice}</p>
        </section>
      )}
    </div>
  );
}
