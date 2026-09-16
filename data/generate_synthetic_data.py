"""MSME Copilot — synthetic dataset generator (fixed seed)."""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import RANDOM_SEED, SAMPLE_DATA_DIR

START = datetime(2024, 1, 1)
DAYS = 90


def generate() -> None:
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    products = pd.DataFrame(
        [
            ["P001", "Steel Bolts M8", "Fasteners", 12.50, 22.00, 500, 7],
            ["P002", "Copper Wire 2mm", "Electrical", 45.00, 78.00, 200, 14],
            ["P003", "PVC Pipe 1inch", "Plumbing", 18.00, 31.00, 300, 5],
            ["P004", "Aluminium Sheet", "Raw Metal", 220.00, 310.00, 50, 21],
            ["P005", "Rubber Gasket Set", "Sealing", 8.00, 19.00, 800, 3],
        ],
        columns=[
            "product_id",
            "product_name",
            "category",
            "unit_cost",
            "selling_price",
            "reorder_point",
            "lead_time_days",
        ],
    )
    products.to_csv(SAMPLE_DATA_DIR / "products.csv", index=False)

    base_demand = {
        "P001": 85,
        "P002": 55,
        "P003": 70,
        "P004": 12,
        "P005": 110,
    }
    seasonal_boost = {
        "P001": [(28, 42, 1.4)],
        "P002": [(28, 42, 1.6), (60, 75, 1.3)],
        "P003": [(0, 14, 0.6), (55, 75, 1.5)],
        "P004": [(35, 50, 1.2)],
        "P005": [(28, 42, 1.5), (70, 90, 1.2)],
    }
    forced_stockout = {"P002": (38, 45)}

    def seasonal_demand(pid: str, day: int, base: int) -> int:
        multiplier = 1.0
        for start, end, boost in seasonal_boost.get(pid, []):
            if start <= day < end:
                multiplier = boost
        raw = base * multiplier
        return int(np.random.normal(raw, raw * 0.12))

    inv_rows = []
    opening_stocks = {"P001": 620, "P002": 420, "P003": 550, "P004": 80, "P005": 950}
    pending_restocks = {pid: [] for pid in products["product_id"]}

    for day in range(DAYS):
        date = (START + timedelta(days=day)).date()
        for _, prod in products.iterrows():
            pid = prod["product_id"]
            stock = opening_stocks[pid]
            received = 0
            still_pending = []
            for arr_day, qty in pending_restocks[pid]:
                if arr_day <= day:
                    received += qty
                else:
                    still_pending.append((arr_day, qty))
            pending_restocks[pid] = still_pending
            stock += received

            if pid in forced_stockout:
                so_start, so_end = forced_stockout[pid]
                if so_start <= day < so_end:
                    sold = min(stock, max(0, seasonal_demand(pid, day, base_demand[pid])))
                    closing = max(0, stock - sold)
                    opening_stocks[pid] = closing
                    inv_rows.append(
                        [date, pid, stock, received, sold, closing, 1 if closing <= 0 else 0]
                    )
                    continue

            sold = min(stock, max(0, seasonal_demand(pid, day, base_demand[pid])))
            closing = stock - sold
            reorder_pt = int(prod["reorder_point"])
            lead = int(prod["lead_time_days"])
            if closing < reorder_pt and not pending_restocks[pid]:
                restock_qty = reorder_pt * 2 + random.randint(-50, 100)
                arrival = day + lead + random.randint(-1, 3)
                pending_restocks[pid].append((arrival, restock_qty))

            stockout = 1 if closing <= 0 else 0
            opening_stocks[pid] = max(0, closing)
            inv_rows.append([date, pid, stock, received, sold, max(0, closing), stockout])

    inventory_df = pd.DataFrame(
        inv_rows,
        columns=[
            "date",
            "product_id",
            "opening_stock",
            "units_received",
            "units_sold",
            "closing_stock",
            "stockout_flag",
        ],
    )
    inventory_df.to_csv(SAMPLE_DATA_DIR / "inventory_movements.csv", index=False)

    suppliers = pd.DataFrame(
        [
            ["S001", "RajMetal Works", "P001", 7, "Net-30", "raj@rajmetal.in"],
            ["S002", "BharatElectro", "P002", 14, "Net-45", "orders@bharatelectro.in"],
            ["S003", "IndoPipe Ltd", "P003", 5, "Net-30", "supply@indopipe.in"],
            ["S004", "MetalCraft India", "P004", 21, "Net-60", "procurement@metalcraft.in"],
            ["S001", "RajMetal Works", "P005", 3, "Net-30", "raj@rajmetal.in"],
        ],
        columns=[
            "supplier_id",
            "supplier_name",
            "product_id",
            "promised_lead_days",
            "payment_terms",
            "contact_email",
        ],
    )
    suppliers.to_csv(SAMPLE_DATA_DIR / "suppliers.csv", index=False)

    delay_profile = {
        "S001": (0.80, 1.5, 4, 0.05),
        "S002": (0.25, 10.0, 16, 0.40),
        "S003": (0.85, 1.0, 3, 0.03),
        "S004": (0.60, 5.0, 14, 0.12),
    }
    order_intervals = {"S001": 18, "S002": 20, "S003": 15, "S004": 25}
    delivery_rows = []
    d_id = 1
    for sid, profile in delay_profile.items():
        on_time_prob, avg_delay, max_delay, short_ship_prob = profile
        sup_products = suppliers[suppliers["supplier_id"] == sid][
            ["product_id", "promised_lead_days"]
        ]
        for _, row in sup_products.iterrows():
            pid = row["product_id"]
            promised_lead = int(row["promised_lead_days"])
            order_day = random.randint(0, 5)
            while order_day < DAYS:
                order_date = START + timedelta(days=order_day)
                promised_date = order_date + timedelta(days=promised_lead)
                if random.random() < on_time_prob:
                    delay = random.randint(0, 2)
                else:
                    delay = min(int(np.random.exponential(avg_delay)) + 1, max_delay)
                actual_date = promised_date + timedelta(days=delay)
                base_qty = products[products["product_id"] == pid]["reorder_point"].values[0] * 2
                qty_ordered = int(base_qty + random.randint(-50, 100))
                if random.random() < short_ship_prob:
                    qty_received = int(qty_ordered * random.uniform(0.75, 0.92))
                else:
                    qty_received = qty_ordered
                delivery_rows.append(
                    [
                        f"D{d_id:03d}",
                        sid,
                        pid,
                        order_date.date(),
                        promised_date.date(),
                        actual_date.date(),
                        qty_ordered,
                        qty_received,
                        delay,
                    ]
                )
                d_id += 1
                order_day += order_intervals[sid] + random.randint(-3, 5)

    deliveries_df = pd.DataFrame(
        delivery_rows,
        columns=[
            "delivery_id",
            "supplier_id",
            "product_id",
            "order_date",
            "promised_date",
            "actual_date",
            "qty_ordered",
            "qty_received",
            "delay_days",
        ],
    )
    deliveries_df.to_csv(SAMPLE_DATA_DIR / "supplier_deliveries.csv", index=False)

    payment_terms_days = {"Net-30": 30, "Net-45": 45, "Net-60": 60}
    invoice_rows = []
    inv_id = 1
    for _, delivery in deliveries_df.iterrows():
        sid = delivery["supplier_id"]
        pid = delivery["product_id"]
        actual_date = datetime.strptime(str(delivery["actual_date"]), "%Y-%m-%d")
        qty = delivery["qty_received"]
        unit_cost = products[products["product_id"] == pid]["unit_cost"].values[0]
        amount = round(qty * unit_cost, 2)
        sup_row = suppliers[
            (suppliers["supplier_id"] == sid) & (suppliers["product_id"] == pid)
        ].iloc[0]
        terms_days = payment_terms_days[sup_row["payment_terms"]]
        due_date = actual_date + timedelta(days=terms_days)
        sim_end = START + timedelta(days=DAYS)
        if due_date > sim_end:
            status = "PENDING"
        elif sid == "S002" and actual_date.month == 2:
            status = "OVERDUE"
        elif due_date < START + timedelta(days=30) and random.random() < 0.15:
            status = "OVERDUE"
        else:
            status = "PAID"
        invoice_rows.append(
            [
                f"INV{inv_id:03d}",
                sid,
                actual_date.date(),
                due_date.date(),
                amount,
                status,
                pid,
                qty,
            ]
        )
        inv_id += 1

    invoices_df = pd.DataFrame(
        invoice_rows,
        columns=[
            "invoice_id",
            "supplier_id",
            "invoice_date",
            "due_date",
            "amount",
            "status",
            "product_id",
            "qty",
        ],
    )
    guaranteed_overdue = pd.DataFrame(
        [
            ["INV_OD1", "S002", "2024-02-10", "2024-03-26", 8550.00, "OVERDUE", "P002", 190],
            ["INV_OD2", "S002", "2024-02-18", "2024-04-03", 9000.00, "OVERDUE", "P002", 200],
            ["INV_OD3", "S004", "2024-02-05", "2024-04-05", 11000.00, "OVERDUE", "P004", 50],
            ["INV_OD4", "S001", "2024-01-28", "2024-02-27", 6250.00, "OVERDUE", "P001", 500],
        ],
        columns=invoices_df.columns,
    )
    invoices_df = pd.concat([invoices_df, guaranteed_overdue], ignore_index=True)
    invoices_df.to_csv(SAMPLE_DATA_DIR / "invoices.csv", index=False)

    machine_notes = [
        "Normal shift, no issues",
        "Minor calibration issue resolved by afternoon",
        "Overtime run, exceeded target",
        "Routine maintenance scheduled",
        "New batch quality check passed",
    ]
    downtime_notes = [
        "Machine breakdown, repaired within shift",
        "Power fluctuation caused 2hr halt",
        "Conveyor belt replacement — 3hr downtime",
        "Hydraulic pressure fault, technician called",
    ]
    prod_rows = []
    planned_units = {"P001": 200, "P002": 120, "P003": 150, "P004": 30, "P005": 300}
    for day in range(DAYS):
        date = (START + timedelta(days=day)).date()
        weekday = (START + timedelta(days=day)).weekday()
        if weekday >= 5:
            continue
        is_monday = weekday == 0
        for pid, planned in planned_units.items():
            seasonal_factor = 1.0
            if pid == "P003" and day >= 55:
                seasonal_factor = 1.3
            if pid == "P002" and 28 <= day < 45:
                seasonal_factor = 1.4
            adj_planned = int(planned * seasonal_factor)
            if pid == "P002" and 38 <= day < 45:
                actual = int(adj_planned * random.uniform(0.1, 0.3))
                defects = random.randint(0, 2)
                downtime = round(random.uniform(2.0, 6.0), 1)
                notes = "Raw material stockout — production severely limited"
            elif is_monday and random.random() < 0.25:
                downtime = round(random.uniform(1.0, 4.0), 1)
                actual = int(adj_planned * random.uniform(0.6, 0.85))
                defects = random.randint(2, 8)
                notes = random.choice(downtime_notes)
            else:
                downtime = round(random.uniform(0, 0.5), 1) if random.random() < 0.1 else 0.0
                actual = int(adj_planned * random.uniform(0.92, 1.08))
                defects = random.randint(0, max(1, int(actual * 0.015)))
                notes = random.choice(machine_notes)
            prod_rows.append([date, pid, adj_planned, actual, defects, downtime, notes])

    prod_df = pd.DataFrame(
        prod_rows,
        columns=[
            "date",
            "product_id",
            "planned_units",
            "actual_units",
            "defect_units",
            "machine_downtime_hrs",
            "operator_notes",
        ],
    )
    prod_df.to_csv(SAMPLE_DATA_DIR / "production_log.csv", index=False)

    cf_rows = []
    balance = 150000.0
    weekly_opex = 8000.0
    inv_weekly = inventory_df.copy()
    inv_weekly["date"] = pd.to_datetime(inv_weekly["date"])
    inv_weekly = inv_weekly.merge(products[["product_id", "selling_price"]], on="product_id")
    inv_weekly["revenue"] = inv_weekly["units_sold"] * inv_weekly["selling_price"]
    inv_weekly["week"] = inv_weekly["date"].dt.isocalendar().week
    inv_paid = invoices_df[invoices_df["status"] == "PAID"].copy()
    inv_paid["due_date"] = pd.to_datetime(inv_paid["due_date"])
    inv_paid["week"] = inv_paid["due_date"].dt.isocalendar().week
    overdue_total = invoices_df[invoices_df["status"] == "OVERDUE"]["amount"].sum()
    crunch_note_fired = False
    recovery_note_fired = False
    for week_offset in range(13):
        week_start = START + timedelta(weeks=week_offset)
        week_num = week_start.isocalendar()[1]
        date = week_start.date()
        week_rev_raw = inv_weekly[inv_weekly["week"] == week_num]["revenue"].sum()
        revenue = round(week_rev_raw * random.uniform(0.65, 0.80), 2)
        supplier_pmts = round(inv_paid[inv_paid["week"] == week_num]["amount"].sum(), 2)
        extra_overdue = 0.0
        notes = ""
        if week_offset in (5, 6, 7) and overdue_total > 0:
            extra_overdue = round(overdue_total / 3 * random.uniform(0.8, 1.2), 2)
            notes = "Overdue invoice cluster — cash pressure"
            if not crunch_note_fired:
                notes = "CASH CRUNCH: Multiple overdue payments due simultaneously"
                crunch_note_fired = True
        if week_offset >= 9 and balance > 120000 and not recovery_note_fired:
            notes = "Cash position recovered — collections normalised"
            recovery_note_fired = True
        total_outflow = supplier_pmts + extra_overdue + weekly_opex
        closing = round(balance + revenue - total_outflow, 2)
        cf_rows.append(
            [
                date,
                round(balance, 2),
                round(revenue, 2),
                round(supplier_pmts + extra_overdue, 2),
                weekly_opex,
                closing,
                notes,
            ]
        )
        balance = max(closing, 0)

    cash_flow_df = pd.DataFrame(
        cf_rows,
        columns=[
            "date",
            "opening_balance",
            "revenue_received",
            "supplier_payments",
            "operating_expenses",
            "closing_balance",
            "notes",
        ],
    )
    cash_flow_df.to_csv(SAMPLE_DATA_DIR / "cash_flow.csv", index=False)

    print(f"Wrote datasets to {SAMPLE_DATA_DIR}")
    print(f"  products.csv {len(products)} rows")
    print(f"  inventory_movements.csv {len(inventory_df)} rows")
    print(f"  suppliers.csv {len(suppliers)} rows")
    print(f"  supplier_deliveries.csv {len(deliveries_df)} rows")
    print(f"  invoices.csv {len(invoices_df)} rows")
    print(f"  production_log.csv {len(prod_df)} rows")
    print(f"  cash_flow.csv {len(cash_flow_df)} rows")


if __name__ == "__main__":
    generate()
