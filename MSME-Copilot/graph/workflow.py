"""LangGraph workflow for MSME Copilot."""

from langgraph.graph import END, START, StateGraph

from agents.business_advisor import run_business_advisor
from agents.document_agent import run_document_agent
from agents.finance_agent import run_finance_agent
from agents.inventory_agent import run_inventory_agent
from agents.supplier_agent import run_supplier_agent
from graph.router import route_after_start
from graph.state import SharedState


def build_workflow() -> StateGraph:
    """Build the LangGraph multi-agent workflow."""
    workflow = StateGraph(SharedState)

    workflow.add_node("document_agent", run_document_agent)
    workflow.add_node("finance_agent", run_finance_agent)
    workflow.add_node("inventory_agent", run_inventory_agent)
    workflow.add_node("supplier_agent", run_supplier_agent)
    workflow.add_node("business_advisor", run_business_advisor)

    workflow.add_conditional_edges(
        START,
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
