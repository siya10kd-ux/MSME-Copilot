"""Finance Agent — cash-flow analysis, payment terms, cost margins."""

import json

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from config.llm import get_llm
from config.prompts import FINANCE_AGENT_PROMPT
from config.settings import SAMPLE_DATA_DIR
from graph.state import SharedState
from tools.csv_parser import load_sample_dataset


def _compute_margins(products: pd.DataFrame) -> list[dict]:
    """Compute profit margins for all products."""
    margins = []
    for _, row in products.iterrows():
        margin = row["selling_price"] - row["unit_cost"]
        margin_pct = round(margin / row["selling_price"] * 100, 1) if row["selling_price"] > 0 else 0
        margins.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "unit_cost": float(row["unit_cost"]),
            "selling_price": float(row["selling_price"]),
            "margin": round(margin, 2),
            "margin_pct": margin_pct,
        })
    return margins


def _analyze_cash_flow(cash_flow: pd.DataFrame) -> dict:
    """Analyze cash flow trends and risks."""
    latest = cash_flow.iloc[-1]
    avg_expenses = cash_flow["operating_expenses"].mean()
    avg_payments = cash_flow["supplier_payments"].mean()
    min_balance = cash_flow["closing_balance"].min()

    recent = cash_flow.tail(4)
    trend = recent["closing_balance"].diff().mean()

    risk_level = "LOW"
    if min_balance < 50000 or trend < -5000:
        risk_level = "HIGH"
    elif min_balance < 100000 or trend < 0:
        risk_level = "MEDIUM"

    return {
        "current_balance": float(latest["closing_balance"]),
        "min_balance_90d": float(min_balance),
        "avg_operating_expenses": round(float(avg_expenses), 2),
        "avg_supplier_payments": round(float(avg_payments), 2),
        "balance_trend": round(float(trend), 2),
        "cash_flow_risk": risk_level,
        "recent_entries": cash_flow.tail(5).to_dict(orient="records"),
    }


def _analyze_invoices(invoices: pd.DataFrame) -> dict:
    """Analyze invoice payment status and overdue amounts."""
    # ── Fix #1: use today's real date instead of the hardcoded 2024-03-31 ─────
    today = pd.Timestamp.today().normalize()
    overdue = invoices[
        (invoices["status"] != "PAID") & (pd.to_datetime(invoices["due_date"]) < today)
    ]
    upcoming = invoices[
        (invoices["status"] != "PAID") & (pd.to_datetime(invoices["due_date"]) >= today)
    ]

    return {
        "total_invoices": len(invoices),
        "paid_count": len(invoices[invoices["status"] == "PAID"]),
        "overdue_count": len(overdue),
        "overdue_amount": round(float(overdue["amount"].sum()), 2),
        "upcoming_payments": round(float(upcoming["amount"].sum()), 2),
        "overdue_invoices": overdue.to_dict(orient="records"),
    }


def run_finance_agent(state: SharedState) -> SharedState:
    """Run cash-flow, payment, and margin analysis."""
    # ── Fix #11: dataset loading is outside try/except so real IO errors
    #             are not silently swallowed as "LLM unavailable" messages ──────
    products = load_sample_dataset("products", SAMPLE_DATA_DIR)
    cash_flow = load_sample_dataset("cash_flow", SAMPLE_DATA_DIR)
    invoices = load_sample_dataset("invoices", SAMPLE_DATA_DIR)

    finance_data = {
        "profit_margins": _compute_margins(products),
        "cash_flow_analysis": _analyze_cash_flow(cash_flow),
        "invoice_analysis": _analyze_invoices(invoices),
    }

    # Only the LLM call is guarded — data errors propagate normally
    try:
        llm = get_llm("finance_agent")
        prompt = ChatPromptTemplate.from_template(FINANCE_AGENT_PROMPT)
        chain = prompt | llm
        response = chain.invoke({
            "finance_data": json.dumps(finance_data, indent=2, default=str)[:4000],
        })
        finance_data["llm_insights"] = response.content
    except Exception as e:
        finance_data["llm_insights"] = f"LLM analysis unavailable: {e}"

    return {**state, "finance_insights": finance_data}
