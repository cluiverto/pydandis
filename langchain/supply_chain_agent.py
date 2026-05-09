from __future__ import annotations
import os
import json
import operator
from typing import Annotated, Sequence, TypedDict, Optional

from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langfuse.langchain import CallbackHandler


langfuse_handler = CallbackHandler()


@tool
def manage_inventory(sku: str = None, **kwargs) -> str:
    """Manage inventory levels, stock replenishment, audits, and optimization strategies."""
    print(f"[TOOL] manage_inventory(sku={sku}, kwargs={kwargs})")
    return "inventory_management_initiated"


@tool
def track_shipments(origin: str = None, **kwargs) -> str:
    """Track shipment status, delays, and coordinate delivery logistics."""
    print(f"[TOOL] track_shipments(origin={origin}, kwargs={kwargs})")
    return "shipment_tracking_updated"


@tool
def evaluate_suppliers(supplier_name: str = None, **kwargs) -> str:
    """Evaluate supplier performance, conduct audits, and manage supplier relationships."""
    print(f"[TOOL] evaluate_suppliers(supplier_name={supplier_name}, kwargs={kwargs})")
    return "supplier_evaluation_complete"


@tool
def optimize_warehouse(operation_type: str = None, **kwargs) -> str:
    """Optimize warehouse operations, layout, capacity, and storage efficiency."""
    print(
        f"[TOOL] optimize_warehouse(operation_type={operation_type}, kwargs={kwargs})"
    )
    return "warehouse_optimization_initiated"


@tool
def forecast_demand(season: str = None, **kwargs) -> str:
    """Analyze demand patterns, seasonal trends, and create forecasting models."""
    print(f"[TOOL] forecast_demand(season={season}, kwargs={kwargs})")
    return "demand_forecast_generated"


@tool
def manage_quality(supplier: str = None, **kwargs) -> str:
    """Manage quality control, defect tracking, and supplier quality standards."""
    print(f"[TOOL] manage_quality(supplier={supplier}, kwargs={kwargs})")
    return "quality_management_initiated"


@tool
def arrange_shipping(shipping_type: str = None, **kwargs) -> str:
    """Arrange shipping methods, expedited delivery, and multi-modal transportation."""
    print(f"[TOOL] arrange_shipping(shipping_type={shipping_type}, kwargs={kwargs})")
    return "shipping_arranged"


@tool
def coordinate_operations(operation_type: str = None, **kwargs) -> str:
    """Coordinate complex operations like cross-docking, consolidation, and transfers."""
    print(
        f"[TOOL] coordinate_operations(operation_type={operation_type}, kwargs={kwargs})"
    )
    return "operations_coordinated"


@tool
def manage_special_handling(product_type: str = None, **kwargs) -> str:
    """Handle special requirements for hazmat, cold chain, and sensitive products."""
    print(
        f"[TOOL] manage_special_handling(product_type={product_type}, kwargs={kwargs})"
    )
    return "special_handling_managed"


@tool
def handle_compliance(compliance_type: str = None, **kwargs) -> str:
    """Manage regulatory compliance, customs, documentation, and certifications."""
    print(
        f"[TOOL] handle_compliance(compliance_type={compliance_type}, kwargs={kwargs})"
    )
    return "compliance_handled"


@tool
def process_returns(returned_quantity: str = None, **kwargs) -> str:
    """Process returns, reverse logistics, and product disposition."""
    print(
        f"[TOOL] process_returns(returned_quantity={returned_quantity}, kwargs={kwargs})"
    )
    return "returns_processed"


@tool
def scale_operations(scaling_type: str = None, **kwargs) -> str:
    """Scale operations for peak seasons, capacity planning, and workforce management."""
    print(f"[TOOL] scale_operations(scaling_type={scaling_type}, kwargs={kwargs})")
    return "operations_scaled"


@tool
def optimize_costs(cost_type: str = None, **kwargs) -> str:
    """Analyze and optimize transportation, storage, and operational costs."""
    print(f"[TOOL] optimize_costs(cost_type={cost_type}, kwargs={kwargs})")
    return "cost_optimization_initiated"


@tool
def optimize_delivery(delivery_type: str = None, **kwargs) -> str:
    """Optimize delivery routes, last-mile logistics, and sustainability initiatives."""
    print(f"[TOOL] optimize_delivery(delivery_type={delivery_type}, kwargs={kwargs})")
    return "delivery_optimization_complete"


@tool
def manage_disruption(disruption_type: str = None, **kwargs) -> str:
    """Manage supply chain disruptions, contingency planning, and risk mitigation."""
    print(
        f"[TOOL] manage_disruption(disruption_type={disruption_type}, kwargs={kwargs})"
    )
    return "disruption_managed"


@tool
def send_logistics_response(operation_id: str = None, message: str = None):
    """Send logistics updates, recommendations, or status reports to stakeholders."""
    print(f"[TOOL] send_logistics_response -> {message}")
    return "logistics_response_sent"


TOOLS = [
    manage_inventory,
    track_shipments,
    evaluate_suppliers,
    optimize_warehouse,
    forecast_demand,
    manage_quality,
    arrange_shipping,
    coordinate_operations,
    manage_special_handling,
    handle_compliance,
    process_returns,
    scale_operations,
    optimize_costs,
    optimize_delivery,
    manage_disruption,
    send_logistics_response,
]


llm = ChatOpenAI(
    model="openrouter/free",
    temperature=0.0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    callbacks=[StreamingStdOutCallbackHandler(), langfuse_handler],
    verbose=True,
).bind_tools(TOOLS)


class AgentState(TypedDict):
    operation: Optional[dict]
    messages: Annotated[Sequence[BaseMessage], operator.add]


def call_model(state: AgentState):
    history = state["messages"]

    operation = state.get("operation", {})
    if not operation:
        operation = {
            "operation_id": "UNKNOWN",
            "type": "general",
            "priority": "medium",
            "status": "active",
        }

    operation_json = json.dumps(operation, ensure_ascii=False)
    system_prompt = (
        "You are an experienced Supply Chain & Logistics professional.\n"
        "Your expertise covers:\n"
        "- Inventory management and demand forecasting\n"
        "- Transportation and shipping optimization\n"
        "- Supplier relationship management and evaluation\n"
        "- Warehouse operations and capacity planning\n"
        "- Quality control and compliance management\n"
        "- Cost optimization and operational efficiency\n"
        "- Risk management and disruption response\n"
        "- Sustainability and green logistics initiatives\n"
        "\n"
        "When managing supply chain operations:\n"
        " 1) Analyze the logistics challenge or opportunity\n"
        " 2) Call the appropriate supply chain management tool\n"
        " 3) Follow up with send_logistics_response to provide recommendations\n"
        " 4) Consider cost, efficiency, quality, and sustainability impacts\n"
        " 5) Prioritize customer satisfaction and business continuity\n"
        "\n"
        "Always balance cost with quality and risk mitigation.\n"
        f"OPERATION: {operation_json}"
    )
    full = [SystemMessage(content=system_prompt)] + history
    first: ToolMessage | BaseMessage = llm.invoke(full)
    messages = [first]

    if getattr(first, "tool_calls", None):
        for tc in first.tool_calls:
            print(first)
            print(tc["name"])
            fn = next(t for t in TOOLS if t.name == tc["name"])
            out = fn.invoke(tc["args"])
            messages.append(ToolMessage(content=str(out), tool_call_id=tc["id"]))
        second = llm.invoke(full + messages)
        messages.append(second)

    return {"messages": messages}


def construct_graph():
    g = StateGraph(AgentState)
    g.add_node("assistant", call_model)
    g.set_entry_point("assistant")
    return g.compile()


graph = construct_graph()


if __name__ == "__main__":
    example = {
        "operation_id": "OP-12345",
        "type": "inventory_management",
        "priority": "high",
        "location": "Warehouse A",
    }
    convo = [
        HumanMessage(
            content="We're running critically low on SKU-12345. Current stock is 50 units but we have 200 units on backorder. What's our reorder strategy?"
        )
    ]
    result = graph.invoke({"operation": example, "messages": convo})
    for m in result["messages"]:
        print(f"{m.type}: {m.content}")
