import asyncio, os
from config import get_model
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from dataclasses import dataclass
from pydantic_ai_backends import LocalBackend, create_console_toolset


backend = LocalBackend("./back")

toolset = create_console_toolset()

async def permission_handler(tool_name, tool_args, reason):
    """Pozwól na wszystko OPRÓCZ config.py i .env"""
    if tool_name in ["write_file", "edit_file"]:
        path = tool_args.get("path", "")
        blocked = ["config.py", ".env", ".git/config"]
        if any(blocked_file in path for blocked_file in blocked):
            print(f"⛔ BLOKUJĘ: {path}")
            return False  # Block
    return True  # Let everything else


async def main():
    # Create a deep agent with all capabilities
    agent = create_deep_agent(
        model=get_model(),
        instructions="You are a helpful coding assistant.",
        interrupt_on={"write_file": False, "edit_file": True},
        permission_handler=permission_handler
    )

    # Create dependencies with in-memory storage
    #deps = DeepAgentDeps(backend=StateBackend())
    # or local backend
    deps = DeepAgentDeps(backend=backend)

    while True:
        user_input = input("\nTy:")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Papa")
            break

        result = await agent.run(user_input, deps=deps)
        print(f"\nAgent: {result.output}")

asyncio.run(main())
