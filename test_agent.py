import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import os


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
model = OpenRouterModel(
    'z-ai/glm-4.5-air:free',
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)


async def main():
    # Create a deep agent with all capabilities
    agent = create_deep_agent(
        model=model,
        instructions="You are a helpful coding assistant.",
    )

    # Create dependencies with in-memory storage
    deps = DeepAgentDeps(backend=StateBackend())

    # Run the agent
    result = await agent.run(
        "Create a Python function that calculates fibonacci numbers",
        deps=deps,
    )

    print(result.output)

asyncio.run(main())
