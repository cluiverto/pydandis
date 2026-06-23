from langchain_openrouter import ChatOpenRouter
from langchain.messages import HumanMessage
from deepagents import create_deep_agent
import os

api_key = os.getenv("OPENROUTER_API_KEY")
model = ChatOpenRouter(model="openrouter/free", temperature=0, max_tokens=1024)


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_deep_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

stream = agent.stream_events(
    {"messages": [HumanMessage(content="what is the weather in sf")]},
    version="v3",
)

for message in stream.messages:
    for chunk in message.reasoning:
        print(f"\r\033[K[thinking] {chunk}", end="", flush=True)
    for chunk in message.text:
        print(chunk, end="", flush=True)
    for chunk in message.tool_calls:
        print(f"\n[tool call chunk] {chunk}")

for call in stream.tool_calls:
    print(f"\n[tool] {call.tool_name}({call.input})", end="", flush=True)
    for delta in call.output_deltas:
        print(delta, end="", flush=True)
    print(f"\n[tool result] {call.output}")

for value in stream.values:
    msgs = value.get("messages", [])
    if msgs:
        last = msgs[-1]
        if hasattr(last, "usage_metadata") and last.usage_metadata:
            print(f"\n[usage] {last.usage_metadata}")
        if hasattr(last, "response_metadata") and last.response_metadata:
            meta = last.response_metadata
            print(
                f"[model] {meta.get('model_name')} | cost: ${meta.get('cost', 0):.6f}"
            )
