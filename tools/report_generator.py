"""Daily production summary report generation."""

from datetime import date
from typing import Any

import pandas as pd

from config.settings import SAMPLE_DATA_DIR
from tools.csv_parser import load_sample_dataset


def generate_daily_summary(target_date: str | None = None) -> dict[str, Any]:
    """Generate a daily production summary for the given date."""
    production = load_sample_dataset("production_log", SAMPLE_DATA_DIR)
    products = load_sample_dataset("products", SAMPLE_DATA_DIR)

    if target_date is None:
        target_date = production["date"].max()

    day_log = production[production["date"] == target_date]
    if day_log.empty:
        return {"date": target_date, "message": "No production data for this date."}

    merged = day_log.merge(products[["product_id", "product_name"]], on="product_id")

    records = []
    total_planned = 0
    total_actual = 0
    total_defects = 0
    total_downtime = 0.0

    for _, row in merged.iterrows():
        efficiency = (
            round(row["actual_units"] / row["planned_units"] * 100, 1)
            if row["planned_units"] > 0
            else 0
        )
        records.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "planned_units": int(row["planned_units"]),
            "actual_units": int(row["actual_units"]),
            "defect_units": int(row["defect_units"]),
            "efficiency_pct": efficiency,
            "downtime_hrs": float(row["machine_downtime_hrs"]),
            "notes": row["operator_notes"],
        })
        total_planned += row["planned_units"]
        total_actual += row["actual_units"]
        total_defects += row["defect_units"]
        total_downtime += row["machine_downtime_hrs"]

    overall_efficiency = (
        round(total_actual / total_planned * 100, 1) if total_planned > 0 else 0
    )

    return {
        "date": target_date,
        "summary": {
            "total_planned": int(total_planned),
            "total_actual": int(total_actual),
            "total_defects": int(total_defects),
            "overall_efficiency_pct": overall_efficiency,
            "total_downtime_hrs": round(total_downtime, 1),
        },
        "products": records,
    }


def format_summary_text(summary: dict[str, Any]) -> str:
    """Format daily summary as readable text."""
    if "message" in summary:
        return summary["message"]

    s = summary["summary"]
    lines = [
        f"DAILY PRODUCTION SUMMARY — {summary['date']}",
        f"Overall Efficiency: {s['overall_efficiency_pct']}%",
        f"Planned: {s['total_planned']} | Actual: {s['total_actual']} | Defects: {s['total_defects']}",
        f"Total Downtime: {s['total_downtime_hrs']} hrs",
        "",
        "Product Details:",
    ]
    for p in summary["products"]:
        lines.append(
            f"  {p['product_name']}: {p['actual_units']}/{p['planned_units']} units "
            f"({p['efficiency_pct']}% eff, {p['defect_units']} defects, "
            f"{p['downtime_hrs']}h downtime)"
        )
        if p["notes"]:
            lines.append(f"    Note: {p['notes']}")
    return "\n".join(lines)
