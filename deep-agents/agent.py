import os , sys
bam_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, bam_dir)
from config import get_openrouter_model

from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend




agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions='You always respond in Italian.',
)
deps = DeepAgentDeps(backend=StateBackend())
agent.to_cli_sync(deps=deps)
