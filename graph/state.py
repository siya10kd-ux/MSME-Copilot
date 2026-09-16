"""Shared LangGraph state for MSME Copilot workflow."""

from typing import Any, Optional, TypedDict


class SharedState(TypedDict, total=False):
    """Shared state passed between agents in the LangGraph workflow."""

    raw_documents: list[dict[str, Any]]
    extracted_data: dict[str, Any]
    finance_insights: dict[str, Any]
    inventory_forecast: dict[str, Any]
    supplier_report: dict[str, Any]
    final_advice: str
    question: str
    skip_document_agent: bool


def create_initial_state(
    question: str = "",
    raw_documents: Optional[list[dict[str, Any]]] = None,
) -> SharedState:
    """Create initial workflow state."""
    docs = raw_documents or []
    return SharedState(
        raw_documents=docs,
        extracted_data={},
        finance_insights={},
        inventory_forecast={},
        supplier_report={},
        final_advice="",
        question=question,
        skip_document_agent=len(docs) == 0,
    )
