import { useState } from "react";
import { uploadDocuments } from "../api.js";

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await uploadDocuments(files, question);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Document upload</h2>
      <p className="muted">Upload invoices, purchase orders, inventory sheets, or production reports.</p>
      <form className="card" onSubmit={onSubmit}>
        <input
          type="file"
          multiple
          onChange={(event) => setFiles(event.target.files)}
        />
        <p>
          <input
            type="text"
            placeholder="Optional question for the Business Advisor"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
        </p>
        <button type="submit" disabled={loading || !files.length}>
          {loading ? "Processing…" : "Upload and extract"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <section className="card" style={{ marginTop: 16 }}>
          <h3>Document Agent result</h3>
          <p className="advice">{result.final_advice}</p>
          <pre className="advice">{JSON.stringify(result.extracted_data, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}
