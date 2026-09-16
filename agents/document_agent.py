"""Document Agent — parses invoices, POs, inventory sheets, production reports."""

import hashlib
import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from config.llm import get_llm
from config.prompts import DOCUMENT_AGENT_PROMPT
from config.settings import SAMPLE_DATA_DIR
from graph.state import SharedState
from db.vector_store import store_document
from tools.csv_parser import load_sample_dataset, parse_inventory_sheet, parse_po_sheet
from tools.ocr_tool import extract_text


def _detect_document_type(filename: str, text: str) -> str:
    """Heuristic document type detection."""
    name_lower = filename.lower()
    text_lower = text.lower()
    if "invoice" in name_lower or "invoice" in text_lower:
        return "invoice"
    if "purchase" in name_lower or "po" in name_lower or "purchase order" in text_lower:
        return "purchase_order"
    if "inventory" in name_lower or "stock" in text_lower:
        return "inventory_sheet"
    if "production" in name_lower or "production" in text_lower:
        return "production_report"
    if filename.endswith(".csv"):
        return "csv_data"
    return "unknown"


def _make_doc_id(filename: str, text: str) -> str:
    # ── Fix #9: use a content hash so same-named files don't overwrite each
    #            other in ChromaDB ─────────────────────────────────────────────
    content_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]
    safe_name = Path(filename).stem[:40]
    return f"{safe_name}-{content_hash}"


def _parse_uploaded_document(doc: dict) -> dict:
    """Parse a single uploaded document."""
    file_path = doc.get("file_path", "")
    filename = doc.get("filename", Path(file_path).name if file_path else "unknown")
    doc_type_hint = doc.get("document_type", "")

    if file_path and Path(file_path).exists():
        text = extract_text(file_path)
        doc_type = doc_type_hint or _detect_document_type(filename, text)
    else:
        text = doc.get("content", "")
        doc_type = doc_type_hint or _detect_document_type(filename, text)

    parsed: dict = {"filename": filename, "document_type": doc_type, "raw_text": text[:3000]}

    if doc_type == "inventory_sheet" and file_path:
        try:
            parsed["structured"] = parse_inventory_sheet(file_path)
        except Exception:
            pass
    elif doc_type == "purchase_order" and file_path:
        try:
            parsed["structured"] = parse_po_sheet(file_path)
        except Exception:
            pass

    return parsed


def _load_invoice_context() -> list[dict]:
    """Load invoice data from sample dataset for context."""
    try:
        invoices = load_sample_dataset("invoices", SAMPLE_DATA_DIR)
        return invoices.to_dict(orient="records")
    except Exception:
        return []


def _load_production_context() -> list[dict]:
    """Load recent production log entries."""
    try:
        production = load_sample_dataset("production_log", SAMPLE_DATA_DIR)
        latest_date = production["date"].max()
        recent = production[production["date"] == latest_date]
        return recent.to_dict(orient="records")
    except Exception:
        return []


def run_document_agent(state: SharedState) -> SharedState:
    """Process uploaded documents and extract structured data."""
    raw_docs = state.get("raw_documents", [])
    parsed_docs = [_parse_uploaded_document(doc) for doc in raw_docs]

    llm = get_llm("document_agent")
    prompt = ChatPromptTemplate.from_template(DOCUMENT_AGENT_PROMPT)

    llm_extractions = []
    for parsed in parsed_docs:
        if parsed.get("raw_text"):
            # ── Fix #11: only the LLM call is inside try/except ───────────────
            try:
                chain = prompt | llm
                response = chain.invoke({
                    "extracted_text": parsed["raw_text"][:2000],
                    "document_type": parsed["document_type"],
                })
                llm_extractions.append({
                    "filename": parsed["filename"],
                    "llm_summary": response.content,
                })
            except Exception as e:
                llm_extractions.append({
                    "filename": parsed["filename"],
                    "llm_summary": f"LLM extraction unavailable: {e}",
                })

    extracted_data = {
        "uploaded_documents": parsed_docs,
        "llm_extractions": llm_extractions,
        "invoices_from_db": _load_invoice_context(),
        "production_from_db": _load_production_context(),
    }

    for parsed in parsed_docs:
        text = parsed.get("raw_text") or ""
        if text:
            # ── Fix #9: use content-hash id to prevent same-name overwrites ───
            doc_id = _make_doc_id(parsed["filename"], text)
            store_document(
                doc_id=doc_id,
                text=text,
                metadata={"document_type": parsed.get("document_type", "unknown"),
                           "filename": parsed["filename"]},
            )

    return {**state, "extracted_data": extracted_data}
