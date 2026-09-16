"""Inventory Agent — forecasting, stockout risk, reorder points."""

import json

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from config.llm import get_llm
from config.prompts import INVENTORY_AGENT_PROMPT
from config.settings import SAMPLE_DATA_DIR
from graph.state import SharedState
from tools.csv_parser import load_sample_dataset


def _forecast_demand(movements: pd.DataFrame, product_id: str, days: int) -> float:
    """Forecast demand for a product over N days based on historical sales."""
    product_data = movements[movements["product_id"] == product_id].sort_values("date")
    if product_data.empty:
        return 0.0
    avg_daily_sales = product_data["units_sold"].mean()
    return round(avg_daily_sales * days, 1)


def _assess_stockout_risk(
    movements: pd.DataFrame, products: pd.DataFrame
) -> list[dict]:
    """Assess stockout risk for each product."""
    latest = movements.sort_values("date").groupby("product_id").last().reset_index()
    merged = latest.merge(products, on="product_id")
    risks = []

    for _, row in merged.iterrows():
        current_stock = row["closing_stock"]
        reorder_point = row["reorder_point"]
        lead_time = row["lead_time_days"]
        demand_30 = _forecast_demand(movements, row["product_id"], 30)
        demand_60 = _forecast_demand(movements, row["product_id"], 60)
        demand_90 = _forecast_demand(movements, row["product_id"], 90)

        days_of_stock = (
            round(current_stock / (row["units_sold"] if row["units_sold"] > 0 else 1), 1)
            if current_stock > 0
            else 0
        )

        risk = "LOW"
        if current_stock <= reorder_point or days_of_stock < lead_time:
            risk = "HIGH"
        elif current_stock <= reorder_point * 1.5:
            risk = "MEDIUM"

        stockout_history = movements[
            (movements["product_id"] == row["product_id"])
            & (movements["stockout_flag"] == 1)
        ]
        stockout_count = len(stockout_history)

        risks.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "current_stock": int(current_stock),
            "reorder_point": int(reorder_point),
            "lead_time_days": int(lead_time),
            "days_of_stock": days_of_stock,
            "demand_forecast_30d": demand_30,
            "demand_forecast_60d": demand_60,
            "demand_forecast_90d": demand_90,
            "stockout_risk": risk,
            "historical_stockouts": stockout_count,
            "needs_reorder": current_stock <= reorder_point,
        })

    return risks


def run_inventory_agent(state: SharedState) -> SharedState:
    """Run inventory forecasting and stockout analysis."""
    movements = load_sample_dataset("inventory_movements", SAMPLE_DATA_DIR)
    products = load_sample_dataset("products", SAMPLE_DATA_DIR)

    stockout_risks = _assess_stockout_risk(movements, products)
    reorder_needed = [r for r in stockout_risks if r["needs_reorder"]]

    inventory_data = {
        "stockout_risks": stockout_risks,
        "reorder_recommendations": reorder_needed,
        "high_risk_products": [r for r in stockout_risks if r["stockout_risk"] == "HIGH"],
    }

    try:
        llm = get_llm("inventory_agent")
        prompt = ChatPromptTemplate.from_template(INVENTORY_AGENT_PROMPT)
        chain = prompt | llm
        response = chain.invoke({
            "inventory_data": json.dumps(inventory_data, indent=2, default=str)[:4000],
        })
        inventory_data["llm_insights"] = response.content
    except Exception as e:
        inventory_data["llm_insights"] = f"LLM analysis unavailable: {e}"

    return {**state, "inventory_forecast": inventory_data}
