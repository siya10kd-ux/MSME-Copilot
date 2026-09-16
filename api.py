"""FastAPI backend for MSME Copilot."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import RAW_DATA_DIR
from db.sqlite_store import get_dashboard_metrics, init_db
from main import run_workflow
from tools.po_generator import generate_purchase_orders
from tools.report_generator import generate_daily_summary

app = FastAPI(title="MSME Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_advice = ""


def _jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str))


@app.on_event("startup")
def startup() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    init_db()
    metrics = get_dashboard_metrics()
    metrics["business_advisor_insights"] = _last_advice
    return _jsonable(metrics)


@app.post("/api/ask")
def ask(payload: dict[str, Any]) -> dict[str, Any]:
    global _last_advice
    question = (payload or {}).get("question", "")
    result = run_workflow(question=question)
    _last_advice = result.get("final_advice", "")
    return _jsonable({
        "question": question,
        "final_advice": result.get("final_advice", ""),
        "finance_insights": result.get("finance_insights", {}),
        "inventory_forecast": result.get("inventory_forecast", {}),
        "supplier_report": result.get("supplier_report", {}),
        "extracted_data": result.get("extracted_data", {}),
    })


@app.post("/api/upload")
async def upload(
    files: list[UploadFile] = File(...),
    question: str = Form(""),
) -> dict[str, Any]:
    global _last_advice
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    documents = []
    for upload in files:
        filename = upload.filename or "upload.bin"
        dest = RAW_DATA_DIR / filename
        dest.write_bytes(await upload.read())
        documents.append({
            "file_path": str(dest),
            "filename": filename,
        })
    result = run_workflow(question=question, documents=documents)
    _last_advice = result.get("final_advice", "")
    return _jsonable({
        "final_advice": result.get("final_advice", ""),
        "extracted_data": result.get("extracted_data", {}),
        "finance_insights": result.get("finance_insights", {}),
        "inventory_forecast": result.get("inventory_forecast", {}),
        "supplier_report": result.get("supplier_report", {}),
    })


@app.get("/api/purchase-orders")
def purchase_orders() -> dict[str, Any]:
    return _jsonable({"purchase_orders": generate_purchase_orders()})


@app.get("/api/reports/daily")
def daily_report() -> dict[str, Any]:
    from tools.report_generator import format_summary_text

    summary = generate_daily_summary()
    return _jsonable({
        "summary": summary,
        "text": format_summary_text(summary),
    })


@app.get("/api/ollama")
def ollama_status() -> dict[str, bool]:
    from config.llm import check_ollama_connection

    return {"ok": check_ollama_connection()}


@app.exception_handler(Exception)
async def unhandled_error(_, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})
