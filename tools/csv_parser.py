"""CSV parsing for inventory sheets and purchase order data."""

from pathlib import Path

import pandas as pd


def parse_csv(file_path: str | Path) -> pd.DataFrame:
    """Parse a CSV file into a DataFrame."""
    return pd.read_csv(file_path)


def parse_inventory_sheet(file_path: str | Path) -> dict:
    """Parse an inventory CSV sheet and return summary stats."""
    df = parse_csv(file_path)
    summary = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "records": df.to_dict(orient="records"),
    }
    if "product_id" in df.columns and "closing_stock" in df.columns:
        summary["products"] = df.groupby("product_id")["closing_stock"].last().to_dict()
    return summary


def parse_po_sheet(file_path: str | Path) -> dict:
    """Parse a purchase order CSV sheet."""
    df = parse_csv(file_path)
    return {
        "total_rows": len(df),
        "columns": list(df.columns),
        "records": df.to_dict(orient="records"),
    }


def load_sample_dataset(name: str, data_dir: Path) -> pd.DataFrame:
    """Load a named sample dataset CSV."""
    path = data_dir / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    return parse_csv(path)
