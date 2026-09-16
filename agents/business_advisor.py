"""Business Advisor — synthesizes agent outputs and answers business questions."""

import json

from langchain_core.prompts import ChatPromptTemplate

from config.llm import get_llm
from config.prompts import BUSINESS_ADVISOR_PROMPT
from graph.state import SharedState
from tools.po_generator import generate_purchase_orders
from tools.report_generator import generate_daily_summary


def _answer_profitable_delayed(finance: dict, supplier: dict) -> list[dict]:
    """Find products that are profitable but frequently delayed."""
    margins = {m["product_id"]: m for m in finance.get("profit_margins", [])}
    results = []

    for score in supplier.get("supplier_scores", []):
        pid = score["product_id"]
        margin = margins.get(pid)
        if margin and margin["margin_pct"] > 30 and score["delay_frequency_pct"] > 20:
            results.append({
                "product_id": pid,
                "product_name": margin["product_name"],
                "margin_pct": margin["margin_pct"],
                "supplier_name": score["supplier_name"],
                "delay_frequency_pct": score["delay_frequency_pct"],
                "reliability_score": score["reliability_score"],
            })

    return sorted(results, key=lambda x: x["margin_pct"], reverse=True)


def run_business_advisor(state: SharedState) -> SharedState:
    """Synthesize all agent outputs and answer the business question."""
    # When Document Agent is skipped, load existing database metrics via the other agents.
    working = dict(state)
    if not working.get("finance_insights"):
        from agents.finance_agent import run_finance_agent

        working = dict(run_finance_agent(working))
    if not working.get("inventory_forecast"):
        from agents.inventory_agent import run_inventory_agent

        working = dict(run_inventory_agent(working))
    if not working.get("supplier_report"):
        from agents.supplier_agent import run_supplier_agent

        working = dict(run_supplier_agent(working))

    finance = working.get("finance_insights", {})
    inventory = working.get("inventory_forecast", {})
    supplier = working.get("supplier_report", {})
    extracted = working.get("extracted_data", {})
    question = working.get("question", "")

    # Pre-compute structured answer for common questions
    structured_answers = {}
    if "profitable" in question.lower() and "delay" in question.lower():
        structured_answers["profitable_delayed_products"] = _answer_profitable_delayed(
            finance, supplier
        )

    # Generate POs and daily summary
    reorder_recs = inventory.get("reorder_recommendations", [])
    purchase_orders = generate_purchase_orders(reorder_recs)
    daily_summary = generate_daily_summary()

    synthesis_context = {
        "structured_answers": structured_answers,
        "purchase_orders": purchase_orders,
        "daily_summary": daily_summary,
    }

    try:
        llm = get_llm("business_advisor")
        prompt = ChatPromptTemplate.from_template(BUSINESS_ADVISOR_PROMPT)
        chain = prompt | llm
        response = chain.invoke({
            "finance_insights": json.dumps(finance, indent=2, default=str)[:2000],
            "inventory_forecast": json.dumps(inventory, indent=2, default=str)[:2000],
            "supplier_report": json.dumps(supplier, indent=2, default=str)[:2000],
            "extracted_data": json.dumps(extracted, indent=2, default=str)[:1000],
            "question": question or "Provide a general business overview.",
        })
        final_advice = response.content
    except Exception as e:
        # Fallback structured response without LLM
        parts = [f"Business Advisor Summary (LLM unavailable: {e})", ""]
        if structured_answers.get("profitable_delayed_products"):
            parts.append("Profitable but frequently delayed products:")
            for p in structured_answers["profitable_delayed_products"]:
                parts.append(
                    f"  - {p['product_name']}: {p['margin_pct']}% margin, "
                    f"{p['delay_frequency_pct']}% delay rate via {p['supplier_name']}"
                )
        if finance.get("cash_flow_analysis"):
            cf = finance["cash_flow_analysis"]
            parts.append(f"\nCash-flow risk: {cf['cash_flow_risk']} "
                         f"(balance: ₹{cf['current_balance']:,.0f})")
        if inventory.get("high_risk_products"):
            parts.append("\nHigh stockout risk products:")
            for p in inventory["high_risk_products"]:
                parts.append(f"  - {p['product_name']}: {p['current_stock']} units "
                             f"(reorder at {p['reorder_point']})")
        final_advice = "\n".join(parts)

    return {
        **working,
        "final_advice": final_advice,
    }
