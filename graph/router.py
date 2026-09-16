"""Conditional routing logic for the LangGraph workflow."""

from graph.state import SharedState


def route_after_start(state: SharedState) -> str:
    """Skip Document Agent when nothing is uploaded; continue with existing data."""
    raw_docs = state.get("raw_documents") or []
    if state.get("skip_document_agent", True) or not raw_docs:
        return "finance_agent"
    return "document_agent"

# ── Fix #4: removed the dead route_after_document() function ─────────────────
#    workflow.py uses a fixed add_edge("document_agent", "finance_agent"),
#    so a conditional router for that transition was never called and is
#    not needed.
