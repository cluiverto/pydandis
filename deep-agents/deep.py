import os, sys
from dotenv import load_dotenv
load_dotenv()

bam_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, bam_dir)
from config import get_openrouter_model

from pydantic_ai import Agent
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend
from langfuse import get_client, propagate_attributes

Agent.instrument_all()

# 2. Deep agent z instrument=True
agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions='You always respond in Italian.',
    include_todo=True,
    instrument=True  
)

deps = DeepAgentDeps(backend=StateBackend())
langfuse = get_client()

# 3. Uruchom CLI z metadanymi Langfuse
with propagate_attributes(
    user_id="deep-user",
    session_id="deep-session",
    tags=["deep-agent"],
):
    agent.to_cli_sync(deps=deps)
