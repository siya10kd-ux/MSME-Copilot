import { useEffect, useState } from "react";
import { fetchPurchaseOrders } from "../api.js";

export default function PurchaseOrders() {
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchPurchaseOrders()
      .then((data) => setOrders(data.purchase_orders || []))
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="error">{error}</p>;

  return (
    <div>
      <h2>Generated purchase orders</h2>
      {!orders.length && <p className="muted">No reorder recommendations right now.</p>}
      <div className="grid">
        {orders.map((po) => (
          <section className="card" key={po.po_id}>
            <h3>{po.po_id}</h3>
            <p><strong>Supplier:</strong> {po.supplier_name}</p>
            <p><strong>Product:</strong> {po.product_name} ({po.product_id})</p>
            <p><strong>Quantity:</strong> {po.quantity}</p>
            <p><strong>Total:</strong> ₹{po.total_amount}</p>
            <p><strong>Payment terms:</strong> {po.payment_terms}</p>
            <p><strong>Expected delivery:</strong> {po.expected_delivery_days} days</p>
          </section>
        ))}
      </div>
    </div>
  );
}
