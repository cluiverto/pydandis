from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

from pathlib import Path
import os, sys
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_openrouter_model
from langfuse import get_client, propagate_attributes



# 1. Najpierw instrumentacja (przed utworzeniem agenta)
Agent.instrument_all()

server = MCPServerStreamableHTTP(os.getenv("ALPHAVANTAGE_URL"))

# 2. Agent z instrument=True
agent = Agent(
    get_openrouter_model(), 
    toolsets=[server],
    instructions='You always respond in Italian.',
    instrument=True
)

# 3. Uruchom z metadanymi
langfuse = get_client()
with propagate_attributes(
    user_id="user_123",
    session_id="session_abc",
    tags=["italian-agent"],
):
    agent.to_cli_sync()

agent.to_cli_sync()