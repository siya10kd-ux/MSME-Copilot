"""LangGraph workflow skeleton for MSME Copilot."""

from langgraph.graph import END, StateGraph

from graph.router import route_after_start
from graph.state import SharedState


def _placeholder_node(state: SharedState) -> SharedState:
    """Placeholder node — replaced by agent implementations in Phase 2/3."""
    return state


def build_workflow() -> StateGraph:
    """Build the LangGraph workflow skeleton."""
    workflow = StateGraph(SharedState)

    # Agent nodes (placeholders until Phase 2/3)
    workflow.add_node("document_agent", _placeholder_node)
    workflow.add_node("finance_agent", _placeholder_node)
    workflow.add_node("inventory_agent", _placeholder_node)
    workflow.add_node("supplier_agent", _placeholder_node)
    workflow.add_node("business_advisor", _placeholder_node)

    # Entry point with conditional routing
    workflow.set_conditional_entry_point(
        route_after_start,
        {
            "document_agent": "document_agent",
            "finance_agent": "finance_agent",
        },
    )

    # Linear workflow after Document Agent
    workflow.add_edge("document_agent", "finance_agent")
    workflow.add_edge("finance_agent", "inventory_agent")
    workflow.add_edge("inventory_agent", "supplier_agent")
    workflow.add_edge("supplier_agent", "business_advisor")
    workflow.add_edge("business_advisor", END)

    return workflow


def compile_workflow():
    """Compile and return the runnable workflow."""
    return build_workflow().compile()
