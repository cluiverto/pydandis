from pydantic_ai import Agent, RunContext
from pydantic_deep import create_deep_agent, create_console_toolset
from pydantic_ai_backends import LocalBackend, StateBackend
from config import get_model
# import asyncio
import httpx

from pydantic_ai_todo import create_todo_toolset


agent = Agent(
    model=get_model(),
    instructions="Pomagasz z informacjami o postaciach z Rick and Morty.",
    toolsets=[create_todo_toolset()]
)

@agent.tool_plain
async def get_all_characters(page: int = 1) -> dict:
    """Pobiera listę postaci z Rick and Morty. Można podać numer strony (domyślnie 1)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://rickandmortyapi.com/api/character",
            params={"page": page}
        )
        response.raise_for_status()
        return response.json()

# async def main():
#     result = await agent.run("Wylistuj postacie z Rick and Morty ze strony 1")
#     print(result.output)

# asyncio.run(main())

agent.to_cli_sync()

