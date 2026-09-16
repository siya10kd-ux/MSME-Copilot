import { useEffect, useState } from "react";
import { fetchDashboard } from "../api.js";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDashboard()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Loading dashboard…</p>;

  const inventoryRows = Object.entries(data.latest_inventory || {}).map(([id, row]) => ({
    product_id: id,
    ...row,
  }));

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="grid">
        <section className="card">
          <h3>Inventory</h3>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Closing stock</th>
                <th>Stockout</th>
              </tr>
            </thead>
            <tbody>
              {inventoryRows.map((row) => (
                <tr key={row.product_id}>
                  <td>{row.product_id}</td>
                  <td>{row.closing_stock}</td>
                  <td>{row.stockout_flag ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="card">
          <h3>Suppliers</h3>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Product</th>
                <th>Lead days</th>
              </tr>
            </thead>
            <tbody>
              {(data.suppliers || []).map((row) => (
                <tr key={`${row.supplier_id}-${row.product_id}`}>
                  <td>{row.supplier_name}</td>
                  <td>{row.product_id}</td>
                  <td>{row.promised_lead_days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="card">
          <h3>Finance</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Closing balance</th>
              </tr>
            </thead>
            <tbody>
              {(data.recent_cash_flow || []).map((row) => (
                <tr key={row.date}>
                  <td>{row.date}</td>
                  <td>{row.closing_balance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="card">
          <h3>Production</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Product</th>
                <th>Actual</th>
              </tr>
            </thead>
            <tbody>
              {(data.recent_production || []).slice(0, 8).map((row, index) => (
                <tr key={`${row.date}-${row.product_id}-${index}`}>
                  <td>{row.date}</td>
                  <td>{row.product_id}</td>
                  <td>{row.actual_units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
      <section className="card" style={{ marginTop: 16 }}>
        <h3>Business Advisor insights</h3>
        <p className="advice">
          {data.business_advisor_insights || "Ask a question on the Business Q&A page to populate insights."}
        </p>
      </section>
    </div>
  );
}
