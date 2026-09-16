"""Conditional routing logic for the LangGraph workflow."""

from graph.state import SharedState


def route_after_start(state: SharedState) -> str:
    """Route from start: skip Document Agent if no documents uploaded."""
    raw_docs = state.get("raw_documents") or []
    if state.get("skip_document_agent", True) or not raw_docs:
        return "business_advisor"
    return "document_agent"


def route_after_document(state: SharedState) -> str:
    """Always proceed to Finance Agent after Document Agent."""
    return "finance_agent"
