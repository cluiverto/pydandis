# agent_mcp_final.py
import os
import asyncio
import sys
from typing import Any, Sequence, Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain_mcp_adapters.client import MultiServerMCPClient
from openrouter_free import FREE_MODELS

# --- Definicja Stanu ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# --- Globalne obiekty ---
mcp_client = None
mcp_tools_cache = None

async def get_mcp_tools():
    """Pobiera narzędzia MCP, inicjalizując klienta jeśli trzeba."""
    global mcp_client, mcp_tools_cache
    
    if mcp_tools_cache is not None:
        return mcp_tools_cache
    
    print("Inicjalizacja MCP client...")
    # Konfiguracja serwerów (ścieżki do skryptów)
    mcp_client = MultiServerMCPClient({
        "math": {
            "command": sys.executable,
            "args": ["mcp_math_server.py"],
            "transport": "stdio",
        },
        "weather": {
            "command": sys.executable,
            "args": ["mcp_weather_server.py"],
            "transport": "stdio",
        }
    })
    
    # Pobranie narzędzi (bez context managera!)
    mcp_tools_cache = await mcp_client.get_tools()
    print(f"Załadowano narzędzia MCP: {[t.name for t in mcp_tools_cache]}")
    return mcp_tools_cache

# --- Model ---
llm = ChatOpenAI(
    model=FREE_MODELS["deepseek_r1"],
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)

# --- Logika Agenta ---
async def call_model(state: AgentState):
    messages = state["messages"]
    print(f"Wywołanie modelu dla: {messages[-1].content[:50]}...")
    
    # Pobierz narzędzia
    tools = await get_mcp_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Wywołanie modelu
    response = await llm_with_tools.ainvoke(messages)
    
    # Obsługa wywołań narzędzi
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_call = response.tool_calls[0]
        print(f"Model wywołał narzędzie: {tool_call['name']}")
        
        # Znajdź odpowiednie narzędzie
        tool_obj = next((t for t in tools if t.name == tool_call["name"]), None)
        if tool_obj:
            # Wywołanie narzędzia
            tool_result = await tool_obj.ainvoke(tool_call)
            print(f"Wynik narzędzia: {tool_result.content[:100]}...")
            return {"messages": [response, tool_result]}
    
    return {"messages": [response]}

# --- Budowa Grafu ---
def construct_graph():
    g = StateGraph(AgentState)
    g.add_node("agent", call_model)
    g.add_edge(START, "agent")
    g.add_edge("agent", END)
    return g.compile()

# --- Testy ---
async def run_tests():
    graph = construct_graph()
    
    # Test 1: Matematyka (wymuszenie użycia narzędzia)
    print("\n=== Test Matematyka ===")
    result_math = await graph.ainvoke({
        "messages": [HumanMessage(content="Użyj narzędzia math do obliczenia (3 + 5) * 12")]
    })
    for msg in result_math["messages"]:
        print(f"{msg.type}: {msg.content}")
    
    print("\n=== Test Pogoda ===")
    # Test 2: Pogoda
    result_weather = await graph.ainvoke({
        "messages": [HumanMessage(content="Jaka jest pogoda w Paryżu? Użyj narzędzia weather.")]
    })
    for msg in result_weather["messages"]:
        print(f"{msg.type}: {msg.content}")

if __name__ == "__main__":
    asyncio.run(run_tests())
