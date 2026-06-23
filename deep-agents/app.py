from langchain_openrouter import ChatOpenRouter
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

result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print(result)