"""Supplier Agent — delay detection, reliability scoring, lead-time analysis."""

import json

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from config.llm import get_llm
from config.prompts import SUPPLIER_AGENT_PROMPT
from config.settings import SAMPLE_DATA_DIR
from graph.state import SharedState
from tools.csv_parser import load_sample_dataset


def _compute_supplier_scores(
    deliveries: pd.DataFrame, suppliers: pd.DataFrame
) -> list[dict]:
    """Compute reliability scores for each supplier."""
    scores = []
    for _, supplier in suppliers.iterrows():
        sid = supplier["supplier_id"]
        pid = supplier["product_id"]
        supplier_deliveries = deliveries[
            (deliveries["supplier_id"] == sid) & (deliveries["product_id"] == pid)
        ]

        if supplier_deliveries.empty:
            continue

        total = len(supplier_deliveries)
        delayed = supplier_deliveries[supplier_deliveries["delay_days"] > 0]
        delay_count = len(delayed)
        avg_delay = round(supplier_deliveries["delay_days"].mean(), 1)
        max_delay = int(supplier_deliveries["delay_days"].max())
        on_time_pct = round((total - delay_count) / total * 100, 1)

        # Reliability score: 100 - (delay_frequency * 30 + avg_delay * 5)
        reliability = max(0, round(100 - (delay_count / total * 30 + avg_delay * 5), 1))

        scores.append({
            "supplier_id": sid,
            "supplier_name": supplier["supplier_name"],
            "product_id": pid,
            "total_deliveries": total,
            "delayed_deliveries": delay_count,
            "delay_frequency_pct": round(delay_count / total * 100, 1),
            "avg_delay_days": avg_delay,
            "max_delay_days": max_delay,
            "on_time_pct": on_time_pct,
            "reliability_score": reliability,
            "promised_lead_days": int(supplier["promised_lead_days"]),
            "payment_terms": supplier["payment_terms"],
        })

    return sorted(scores, key=lambda x: x["reliability_score"])


def _identify_delayed_suppliers(scores: list[dict]) -> list[dict]:
    """Return suppliers with reliability issues."""
    return [s for s in scores if s["reliability_score"] < 70 or s["delayed_deliveries"] > 0]


def run_supplier_agent(state: SharedState) -> SharedState:
    """Run supplier delay detection and reliability analysis."""
    deliveries = load_sample_dataset("supplier_deliveries", SAMPLE_DATA_DIR)
    suppliers = load_sample_dataset("suppliers", SAMPLE_DATA_DIR)

    scores = _compute_supplier_scores(deliveries, suppliers)
    delayed = _identify_delayed_suppliers(scores)

    supplier_data = {
        "supplier_scores": scores,
        "delayed_suppliers": delayed,
        "worst_performers": scores[:3] if scores else [],
    }

    try:
        llm = get_llm("supplier_agent")
        prompt = ChatPromptTemplate.from_template(SUPPLIER_AGENT_PROMPT)
        chain = prompt | llm
        response = chain.invoke({
            "supplier_data": json.dumps(supplier_data, indent=2, default=str)[:4000],
        })
        supplier_data["llm_insights"] = response.content
    except Exception as e:
        supplier_data["llm_insights"] = f"LLM analysis unavailable: {e}"

    return {**state, "supplier_report": supplier_data}
