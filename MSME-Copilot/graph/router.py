"""Conditional routing logic for the LangGraph workflow."""

from graph.state import SharedState


def route_after_start(state: SharedState) -> str:
    """Skip Document Agent when nothing is uploaded; continue with existing data."""
    raw_docs = state.get("raw_documents") or []
    if state.get("skip_document_agent", True) or not raw_docs:
        return "finance_agent"
    return "document_agent"


def route_after_document(state: SharedState) -> str:
    """Always proceed to Finance Agent after Document Agent."""
    return "finance_agent"
