"""Conditional routing logic for the LangGraph workflow."""

from graph.state import SharedState


def route_after_start(state: SharedState) -> str:
    """Route from start: skip Document Agent if no documents uploaded."""
    if state.get("skip_document_agent", True):
        return "finance_agent"
    return "document_agent"


def route_after_document(state: SharedState) -> str:
    """Always proceed to Finance Agent after Document Agent."""
    return "finance_agent"
