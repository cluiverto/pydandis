from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend
from pydantic_ai.mcp import MCPServerStreamableHTTP
from dotenv import load_dotenv
import os , sys

# Pobierz katalog główny bam wzgledem obecnego folderu roboczego
bam_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, bam_dir)
from config import get_openrouter_model

agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions='You always respond in Italian.',
)
deps = DeepAgentDeps(backend=StateBackend())
agent.to_cli_sync(deps=deps)
