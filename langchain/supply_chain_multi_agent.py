from __future__ import annotations
import os, json, operator
from typing import Annotated, Sequence, TypedDict, Optional

from dotenv import load_dotenv
load_dotenv()

from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import (
    AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage,
)
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler()


# ─── SHARED TOOL ─────────────────────────────────────────────────

@tool
def send_logistics_response(operation_id: str = None, message: str = None):
    """Send logistics updates, recommendations, or status reports to stakeholders."""
    print(f"[TOOL] send_logistics_response -> {message}")
    return "logistics_response_sent"


# ─── INVENTORY & WAREHOUSE TOOLS ─────────────────────────────────

@tool
def manage_inventory(sku: str = None, **kwargs) -> str:
    """Manage inventory levels, stock replenishment, audits, and optimization strategies."""
    print(f"[TOOL] manage_inventory(sku={sku}, kwargs={kwargs})")
    return "inventory_management_initiated"

@tool
def optimize_warehouse(operation_type: str = None, **kwargs) -> str:
    """Optimize warehouse operations, layout, capacity, and storage efficiency."""
    print(f"[TOOL] optimize_warehouse(operation_type={operation_type}, kwargs={kwargs})")
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
def scale_operations(scaling_type: str = None, **kwargs) -> str:
    """Scale operations for peak seasons, capacity planning, and workforce management."""
    print(f"[TOOL] scale_operations(scaling_type={scaling_type}, kwargs={kwargs})")
    return "operations_scaled"

@tool
def optimize_costs(cost_type: str = None, **kwargs) -> str:
    """Analyze and optimize transportation, storage, and operational costs."""
    print(f"[TOOL] optimize_costs(cost_type={cost_type}, kwargs={kwargs})")
    return "cost_optimization_initiated"

INVENTORY_TOOLS = [
    manage_inventory, optimize_warehouse, forecast_demand,
    manage_quality, scale_operations, optimize_costs, send_logistics_response,
]


# ─── TRANSPORTATION & LOGISTICS TOOLS ────────────────────────────

@tool
def track_shipments(origin: str = None, **kwargs) -> str:
    """Track shipment status, delays, and coordinate delivery logistics."""
    print(f"[TOOL] track_shipments(origin={origin}, kwargs={kwargs})")
    return "shipment_tracking_updated"

@tool
def arrange_shipping(shipping_type: str = None, **kwargs) -> str:
    """Arrange shipping methods, expedited delivery, and multi-modal transportation."""
    print(f"[TOOL] arrange_shipping(shipping_type={shipping_type}, kwargs={kwargs})")
    return "shipping_arranged"

@tool
def coordinate_operations(operation_type: str = None, **kwargs) -> str:
    """Coordinate complex operations like cross-docking, consolidation, and transfers."""
    print(f"[TOOL] coordinate_operations(operation_type={operation_type}, kwargs={kwargs})")
    return "operations_coordinated"

@tool
def manage_special_handling(product_type: str = None, **kwargs) -> str:
    """Handle special requirements for hazmat, cold chain, and sensitive products."""
    print(f"[TOOL] manage_special_handling(product_type={product_type}, kwargs={kwargs})")
    return "special_handling_managed"

@tool
def process_returns(returned_quantity: str = None, **kwargs) -> str:
    """Process returns, reverse logistics, and product disposition."""
    print(f"[TOOL] process_returns(returned_quantity={returned_quantity}, kwargs={kwargs})")
    return "returns_processed"

@tool
def optimize_delivery(delivery_type: str = None, **kwargs) -> str:
    """Optimize delivery routes, last-mile logistics, and sustainability initiatives."""
    print(f"[TOOL] optimize_delivery(delivery_type={delivery_type}, kwargs={kwargs})")
    return "delivery_optimization_complete"

@tool
def manage_disruption(disruption_type: str = None, **kwargs) -> str:
    """Manage supply chain disruptions, contingency planning, and risk mitigation."""
    print(f"[TOOL] manage_disruption(disruption_type={disruption_type}, kwargs={kwargs})")
    return "disruption_managed"

TRANSPORTATION_TOOLS = [
    track_shipments, arrange_shipping, coordinate_operations,
    manage_special_handling, process_returns, optimize_delivery,
    manage_disruption, send_logistics_response,
]


# ─── SUPPLIER & COMPLIANCE TOOLS ─────────────────────────────────

@tool
def evaluate_suppliers(supplier_name: str = None, **kwargs) -> str:
    """Evaluate supplier performance, conduct audits, and manage supplier relationships."""
    print(f"[TOOL] evaluate_suppliers(supplier_name={supplier_name}, kwargs={kwargs})")
    return "supplier_evaluation_complete"

@tool
def handle_compliance(compliance_type: str = None, **kwargs) -> str:
    """Manage regulatory compliance, customs, documentation, and certifications."""
    print(f"[TOOL] handle_compliance(compliance_type={compliance_type}, kwargs={kwargs})")
    return "compliance_handled"

SUPPLIER_TOOLS = [evaluate_suppliers, handle_compliance, send_logistics_response]


# ─── LLM (OpenRouter jak w single) ───────────────────────────────

llm = ChatOpenAI(
    model="openrouter/free",
    temperature=0.0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    verbose=True,
    callbacks=[langfuse_handler],
)

inventory_llm = llm.bind_tools(INVENTORY_TOOLS)
transportation_llm = llm.bind_tools(TRANSPORTATION_TOOLS)
supplier_llm = llm.bind_tools(SUPPLIER_TOOLS)

ALL_TOOLS = INVENTORY_TOOLS + TRANSPORTATION_TOOLS + SUPPLIER_TOOLS
tool_map = {t.name: t for t in ALL_TOOLS}


# ─── GRAF ────────────────────────────────────────────────────────

class AgentState(TypedDict):
    operation: Optional[dict]
    messages: Annotated[Sequence[BaseMessage], operator.add]
    specialist: Optional[str]


def call_node(llm, state, specialist_name):
    history = state["messages"]
    operation = state.get("operation", {})
    op_json = json.dumps(operation, ensure_ascii=False)
    system = (
        "You are an experienced Supply Chain & Logistics professional.\n"
        "Use the available tools to handle the request.\n"
        "Always follow up with send_logistics_response.\n"
        f"OPERATION: {op_json}"
    )
    result = llm.invoke([SystemMessage(content=system)] + history)
    msgs = [result]
    if getattr(result, "tool_calls", None):
        for tc in result.tool_calls:
            fn = tool_map[tc["name"]]
            out = fn.invoke(tc["args"])
            msgs.append(ToolMessage(content=str(out), tool_call_id=tc["id"]))
        second = llm.invoke([SystemMessage(content=system)] + history + msgs)
        msgs.append(second)
    return {"messages": msgs, "specialist": specialist_name}


def call_inventory(state):     return call_node(inventory_llm, state, "inventory")
def call_transportation(state): return call_node(transportation_llm, state, "transportation")
def call_supplier(state):       return call_node(supplier_llm, state, "supplier")


def router(state):
    last = state["messages"][-1] if state["messages"] else None
    c = (last.content or "").lower() if last and hasattr(last, "content") and last.content else ""
    if any(w in c for w in ["inventory", "stock", "warehouse", "sku",
                            "replenishment", "audit", "quality", "demand", "forecast"]):
        return "inventory"
    if any(w in c for w in ["shipment", "shipping", "delivery", "transport",
                            "return", "disruption", "route", "cross-dock"]):
        return "transportation"
    if any(w in c for w in ["supplier", "vendor", "compliance", "customs",
                            "regulatory", "certification", "audit"]):
        return "supplier"
    return "inventory"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("inventory", call_inventory)
    g.add_node("transportation", call_transportation)
    g.add_node("supplier", call_supplier)
    g.set_conditional_entry_point(router, {
        "inventory": "inventory",
        "transportation": "transportation",
        "supplier": "supplier",
    })
    g.add_edge("inventory", END)
    g.add_edge("transportation", END)
    g.add_edge("supplier", END)
    return g.compile()


graph = build_graph()


if __name__ == "__main__":
    example = {
        "operation_id": "OP-12345",
        "type": "inventory_management",
        "priority": "high",
        "location": "Warehouse A",
    }
    queries = [
        "We're running critically low on SKU-12345. Current stock is 50 units but we have 200 units on backorder. What's our reorder strategy?",
        "We need to arrange urgent shipping for a cold chain shipment from Poland to Germany.",
        "Evaluate supplier Acme Corp for quality and compliance issues.",
    ]
    for q in queries:
        print(f"\n{'='*60}")
        print(f">> {q}")
        print("="*60)
        r = graph.invoke({"operation": example, "messages": [HumanMessage(content=q)]})
        for m in r["messages"]:
            if hasattr(m, "content") and m.content:
                print(f"[{m.type}] {m.content[:300]}")
