"""SQLite store for structured business metrics."""

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import SAMPLE_DATA_DIR, SQLITE_PATH


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection, creating the DB if needed."""
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite database with sample datasets."""
    conn = get_connection()
    datasets = [
        "products", "inventory_movements", "suppliers",
        "supplier_deliveries", "invoices", "production_log", "cash_flow",
    ]
    for name in datasets:
        path = SAMPLE_DATA_DIR / f"{name}.csv"
        if path.exists():
            df = pd.read_csv(path)
            df.to_sql(name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a SQL query and return results as list of dicts."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_dashboard_metrics() -> dict[str, Any]:
    """Return aggregated metrics for the dashboard."""
    conn = get_connection()

    products = pd.read_sql("SELECT * FROM products", conn) if _table_exists(conn, "products") else pd.DataFrame()
    inventory = pd.read_sql(
        "SELECT * FROM inventory_movements ORDER BY date DESC", conn
    ) if _table_exists(conn, "inventory_movements") else pd.DataFrame()
    suppliers = pd.read_sql("SELECT * FROM suppliers", conn) if _table_exists(conn, "suppliers") else pd.DataFrame()
    cash_flow = pd.read_sql(
        "SELECT * FROM cash_flow ORDER BY date DESC LIMIT 5", conn
    ) if _table_exists(conn, "cash_flow") else pd.DataFrame()
    production = pd.read_sql(
        "SELECT * FROM production_log ORDER BY date DESC LIMIT 10", conn
    ) if _table_exists(conn, "production_log") else pd.DataFrame()

    conn.close()

    latest_inventory = {}
    if not inventory.empty:
        latest = inventory.sort_values("date").groupby("product_id").last()
        latest_inventory = latest[["closing_stock", "stockout_flag"]].to_dict(orient="index")

    return {
        "products": products.to_dict(orient="records") if not products.empty else [],
        "latest_inventory": latest_inventory,
        "suppliers": suppliers.to_dict(orient="records") if not suppliers.empty else [],
        "recent_cash_flow": cash_flow.to_dict(orient="records") if not cash_flow.empty else [],
        "recent_production": production.to_dict(orient="records") if not production.empty else [],
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cursor.fetchone() is not None
