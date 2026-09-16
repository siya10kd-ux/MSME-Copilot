"""Purchase order generation tool."""

from datetime import date
from typing import Any

import pandas as pd

from config.settings import SAMPLE_DATA_DIR
from tools.csv_parser import load_sample_dataset


def generate_purchase_orders(
    reorder_recommendations: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generate purchase orders based on reorder recommendations."""
    products = load_sample_dataset("products", SAMPLE_DATA_DIR)
    suppliers = load_sample_dataset("suppliers", SAMPLE_DATA_DIR)

    if not reorder_recommendations:
        # Default: products below reorder point
        movements = load_sample_dataset("inventory_movements", SAMPLE_DATA_DIR)
        latest = movements.sort_values("date").groupby("product_id").last().reset_index()
        merged = latest.merge(products, on="product_id")
        reorder_recommendations = []
        for _, row in merged.iterrows():
            if row["closing_stock"] <= row["reorder_point"]:
                reorder_recommendations.append({
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "current_stock": int(row["closing_stock"]),
                    "reorder_point": int(row["reorder_point"]),
                    "order_qty": int(row["reorder_point"] * 2 - row["closing_stock"]),
                })

    purchase_orders = []
    today = date.today().isoformat()

    for rec in reorder_recommendations:
        product_id = rec["product_id"]
        supplier_row = suppliers[suppliers["product_id"] == product_id]
        if supplier_row.empty:
            continue
        supplier = supplier_row.iloc[0]
        order_qty = rec.get("order_qty", rec.get("reorder_point", 100))
        unit_cost = products[products["product_id"] == product_id]["unit_cost"].iloc[0]

        po = {
            "po_id": f"PO-{product_id}-{today.replace('-', '')}",
            "date": today,
            "supplier_id": supplier["supplier_id"],
            "supplier_name": supplier["supplier_name"],
            "product_id": product_id,
            "product_name": rec.get("product_name", product_id),
            "quantity": order_qty,
            "unit_cost": float(unit_cost),
            "total_amount": round(order_qty * unit_cost, 2),
            "payment_terms": supplier["payment_terms"],
            "expected_delivery_days": int(supplier["promised_lead_days"]),
            "contact_email": supplier["contact_email"],
        }
        purchase_orders.append(po)

    return purchase_orders


def format_po_text(po: dict[str, Any]) -> str:
    """Format a purchase order as readable text."""
    return (
        f"PURCHASE ORDER: {po['po_id']}\n"
        f"Date: {po['date']}\n"
        f"Supplier: {po['supplier_name']} ({po['supplier_id']})\n"
        f"Product: {po['product_name']} ({po['product_id']})\n"
        f"Quantity: {po['quantity']}\n"
        f"Unit Cost: ₹{po['unit_cost']:.2f}\n"
        f"Total: ₹{po['total_amount']:.2f}\n"
        f"Payment Terms: {po['payment_terms']}\n"
        f"Expected Delivery: {po['expected_delivery_days']} days\n"
        f"Contact: {po['contact_email']}\n"
    )
