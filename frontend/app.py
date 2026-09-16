"""Streamlit UI for MSME Copilot. Calls backend modules; does not host agents."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config.settings import RAW_DATA_DIR
from db.sqlite_store import get_dashboard_metrics, init_db
from tools.po_generator import format_po_text, generate_purchase_orders
from tools.report_generator import format_summary_text, generate_daily_summary

st.set_page_config(page_title="MSME Copilot", layout="wide")


def _init() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    if "last_advice" not in st.session_state:
        st.session_state.last_advice = ""


def _check_ollama() -> bool:
    """Return True if Ollama is reachable."""
    from config.llm import check_ollama_connection
    return check_ollama_connection()


# ─────────────────────────────────────────────────────────────────────────────
# FIXED page_upload — shows per-step progress so the UI never looks frozen
# ─────────────────────────────────────────────────────────────────────────────
def page_upload() -> None:
    st.header("Document upload")
    st.caption("Upload invoices, purchase orders, inventory sheets, or production reports.")

    files = st.file_uploader(
        "Documents",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg", "csv", "txt"],
    )
    question = st.text_input("Optional question for the Business Advisor")

    if not st.button("Upload and extract", disabled=not files):
        return

    # ── Fix: check Ollama BEFORE starting — fail fast instead of hanging ─────
    with st.spinner("Checking Ollama connection…"):
        if not _check_ollama():
            st.error(
                "❌ Cannot reach Ollama at http://localhost:11434.\n\n"
                "Make sure Ollama is running (`ollama serve`) and the model is pulled:\n"
                "```\nollama pull qwen2.5-coder:7b-instruct\n```"
            )
            return

    # ── Step 1: Save uploaded files ───────────────────────────────────────────
    documents = []
    with st.spinner("💾 Saving uploaded files…"):
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        for upload in files:
            dest = RAW_DATA_DIR / upload.name
            dest.write_bytes(upload.getbuffer())
            documents.append({"file_path": str(dest), "filename": upload.name})
    st.success(f"✅ Saved {len(documents)} file(s)")

    # ── Step 2: OCR / text extraction (no LLM yet) ────────────────────────────
    extracted_texts = {}
    with st.spinner("📄 Extracting text from documents (OCR)…"):
        from tools.ocr_tool import extract_text
        for doc in documents:
            extracted_texts[doc["filename"]] = extract_text(doc["file_path"])
    st.success("✅ Text extraction complete")

    # ── Step 3: Document Agent (1 LLM call per file) ──────────────────────────
    with st.spinner("🤖 Document Agent: parsing document fields with LLM…"):
        from agents.document_agent import run_document_agent
        from graph.state import create_initial_state
        state = create_initial_state(question=question, raw_documents=documents)
        state = run_document_agent(state)
    st.success("✅ Document Agent done")

    # ── Step 4: Finance Agent ─────────────────────────────────────────────────
    with st.spinner("💰 Finance Agent: analysing cash flow and margins…"):
        from agents.finance_agent import run_finance_agent
        state = run_finance_agent(state)
    st.success("✅ Finance Agent done")

    # ── Step 5: Inventory Agent ───────────────────────────────────────────────
    with st.spinner("📦 Inventory Agent: forecasting stockout risks…"):
        from agents.inventory_agent import run_inventory_agent
        state = run_inventory_agent(state)
    st.success("✅ Inventory Agent done")

    # ── Step 6: Supplier Agent ────────────────────────────────────────────────
    with st.spinner("🚚 Supplier Agent: scoring supplier reliability…"):
        from agents.supplier_agent import run_supplier_agent
        state = run_supplier_agent(state)
    st.success("✅ Supplier Agent done")

    # ── Step 7: Business Advisor (final synthesis) ────────────────────────────
    with st.spinner("🧠 Business Advisor: synthesising final answer…"):
        from agents.business_advisor import run_business_advisor
        state = run_business_advisor(state)
    st.success("✅ Business Advisor done")

    # ── Render results ────────────────────────────────────────────────────────
    result = dict(state)
    st.session_state.last_advice = result.get("final_advice", "")

    st.subheader("Business Advisor answer")
    st.write(result.get("final_advice", "No answer generated."))

    with st.expander("Extracted document data"):
        st.json(result.get("extracted_data", {}))

    with st.expander("Finance insights"):
        st.json(result.get("finance_insights", {}))

    with st.expander("Inventory forecast"):
        st.json(result.get("inventory_forecast", {}))

    with st.expander("Supplier report"):
        st.json(result.get("supplier_report", {}))


# ─────────────────────────────────────────────────────────────────────────────
# Rest of pages (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def page_dashboard() -> None:
    st.header("Dashboard")
    metrics = get_dashboard_metrics()

    inventory_rows = [
        {"product_id": pid, "closing_stock": vals.get("closing_stock"), "stockout_flag": vals.get("stockout_flag")}
        for pid, vals in (metrics.get("latest_inventory") or {}).items()
    ]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inventory")
        st.dataframe(pd.DataFrame(inventory_rows), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Suppliers")
        suppliers = pd.DataFrame(metrics.get("suppliers") or [])
        if not suppliers.empty:
            st.dataframe(
                suppliers[["supplier_name", "product_id", "promised_lead_days"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No supplier data.")

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Finance")
        cash = pd.DataFrame(metrics.get("recent_cash_flow") or [])
        if not cash.empty:
            st.dataframe(
                cash[["date", "closing_balance"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No cash-flow data.")
    with col4:
        st.subheader("Production")
        prod = pd.DataFrame(metrics.get("recent_production") or [])
        if not prod.empty:
            st.dataframe(
                prod[["date", "product_id", "actual_units"]].head(8),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No production data.")

    st.subheader("Business Advisor insights")
    st.write(st.session_state.last_advice or "Ask a question on the Business Q&A page to populate insights.")


def page_ask() -> None:
    st.header("Business Q&A")
    question = st.text_area(
        "Question",
        value="Which products are profitable but frequently delayed?",
        height=120,
    )
    if st.button("Ask Business Advisor", disabled=not question.strip()):
        if not _check_ollama():
            st.error("❌ Cannot reach Ollama. Run `ollama serve` and pull the model first.")
            return
        with st.spinner("🧠 Running multi-agent workflow…"):
            from main import run_workflow
            result = run_workflow(question=question.strip())
        st.session_state.last_advice = result.get("final_advice", "")
        st.subheader("Answer")
        st.write(result.get("final_advice", ""))


def page_purchase_orders() -> None:
    st.header("Generated purchase orders")
    orders = generate_purchase_orders()
    if not orders:
        st.info("No reorder recommendations right now.")
        return
    for po in orders:
        with st.container(border=True):
            st.subheader(po["po_id"])
            st.write(f"**Supplier:** {po['supplier_name']}")
            st.write(f"**Product:** {po['product_name']} ({po['product_id']})")
            st.write(f"**Quantity:** {po['quantity']}")
            st.write(f"**Total:** ₹{po['total_amount']}")
            st.write(f"**Payment terms:** {po['payment_terms']}")
            st.write(f"**Expected delivery:** {po['expected_delivery_days']} days")
            st.code(format_po_text(po), language=None)


def page_reports() -> None:
    st.header("Daily production summary")
    summary = generate_daily_summary()
    st.code(format_summary_text(summary), language=None)


def main() -> None:
    _init()
    st.sidebar.title("MSME Copilot")
    st.sidebar.caption("Operations agent for small manufacturers")
    page = st.sidebar.radio(
        "Go to",
        [
            "Dashboard",
            "Document upload",
            "Business Q&A",
            "Purchase orders",
            "Daily summaries",
        ],
    )
    if page == "Dashboard":
        page_dashboard()
    elif page == "Document upload":
        page_upload()
    elif page == "Business Q&A":
        page_ask()
    elif page == "Purchase orders":
        page_purchase_orders()
    else:
        page_reports()


if __name__ == "__main__":
    main()