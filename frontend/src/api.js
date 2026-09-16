async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export function fetchDashboard() {
  return request("/api/dashboard");
}

export function askQuestion(question) {
  return request("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function uploadDocuments(files, question = "") {
  const form = new FormData();
  Array.from(files).forEach((file) => form.append("files", file));
  form.append("question", question);
  return request("/api/upload", { method: "POST", body: form });
}

export function fetchPurchaseOrders() {
  return request("/api/purchase-orders");
}

export function fetchDailyReport() {
  return request("/api/reports/daily");
}
