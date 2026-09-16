import { NavLink, Route, Routes } from "react-router-dom";
import Ask from "./pages/Ask.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import PurchaseOrders from "./pages/PurchaseOrders.jsx";
import Reports from "./pages/Reports.jsx";
import Upload from "./pages/Upload.jsx";

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <h1>MSME Copilot</h1>
        <p className="tagline">Operations agent for small manufacturers</p>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/upload">Document upload</NavLink>
          <NavLink to="/ask">Business Q&amp;A</NavLink>
          <NavLink to="/purchase-orders">Purchase orders</NavLink>
          <NavLink to="/reports">Daily summaries</NavLink>
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/ask" element={<Ask />} />
          <Route path="/purchase-orders" element={<PurchaseOrders />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </main>
    </div>
  );
}
