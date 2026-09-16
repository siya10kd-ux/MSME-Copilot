"""FastAPI backend for MSME Copilot."""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import RAW_DATA_DIR
from db.sqlite_store import get_dashboard_metrics, init_db
from main import run_workflow
from tools.po_generator import generate_purchase_orders
from tools.report_generator import generate_daily_summary


# ── Fix #5: use lifespan instead of deprecated @app.on_event("startup") ──────
@asynccontextmanager
async def lifespan(app: FastAPI):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="MSME Copilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Fix #3: removed module-level _last_advice global ─────────────────────────
#    Each endpoint now returns advice directly from the workflow result,
#    so concurrent requests no longer overwrite each other's state.


def _jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str))


# ── Fix #10: use a Pydantic model so FastAPI can parse the JSON body ──────────
class AskPayload(BaseModel):
    question: str = ""


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    # ── Fix #13: init_db() is NOT called here; it already ran at startup ──────
    metrics = get_dashboard_metrics()
    return _jsonable(metrics)


@app.post("/api/ask")
def ask(payload: AskPayload) -> dict[str, Any]:
    result = run_workflow(question=payload.question)
    # ── Fix #3: advice is local to this request, not stored in a global ───────
    return _jsonable({
        "question": payload.question,
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
