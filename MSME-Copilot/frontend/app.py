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


def page_upload() -> None:
    st.header("Document upload")
    st.caption("Upload invoices, purchase orders, inventory sheets, or production reports.")
    files = st.file_uploader(
        "Documents",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg", "csv", "txt"],
    )
    question = st.text_input("Optional question for the Business Advisor")
    if st.button("Upload and extract", disabled=not files):
        documents = []
        for upload in files:
            dest = RAW_DATA_DIR / upload.name
            dest.write_bytes(upload.getbuffer())
            documents.append({"file_path": str(dest), "filename": upload.name})
        from main import run_workflow

        result = run_workflow(question=question, documents=documents)
        st.session_state.last_advice = result.get("final_advice", "")
        st.subheader("Document Agent result")
        st.write(result.get("final_advice", ""))
        st.json(result.get("extracted_data", {}))


def page_ask() -> None:
    st.header("Business Q&A")
    question = st.text_area(
        "Question",
        value="Which products are profitable but frequently delayed?",
        height=120,
    )
    if st.button("Ask Business Advisor", disabled=not question.strip()):
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
