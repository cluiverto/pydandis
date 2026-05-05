import os, sys
from dotenv import load_dotenv
load_dotenv()

bam_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, bam_dir)
from config import get_openrouter_model

from pydantic_ai import Agent, RunContext
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend, LocalBackend
from langfuse import get_client, propagate_attributes

import json


#langfuse (init)
Agent.instrument_all()


#tool
async def add_italian_word(ctx: RunContext[DeepAgentDeps], word: str, translation: str) -> str:
    """Add a word to the Italian vocabulary list (saved as JSON)."""
    vocab_path = "italian_vocab.json"  # <-- bez ukośnika, zapisze w katalogu roboczym
    try:
        content = await ctx.deps.backend.read_file(vocab_path)
        vocab = json.loads(content)
    except:
        vocab = []
    vocab.append({"word": word, "translation": translation})
    await ctx.deps.backend.write_file(vocab_path, json.dumps(vocab, indent=2, ensure_ascii=False))
    return f"Added: {word} = {translation} (saved to {vocab_path})"



#agent
agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions='You always respond in Italian.',
    include_todo=True,
    skill_directories=["skills"],
    instrument=True  
)

deps = DeepAgentDeps(backend=LocalBackend("."))
langfuse = get_client()

# CLI z metadanymi Langfuse
with propagate_attributes(
    user_id="deep-user",
    session_id="deep-session",
    tags=["deep-agent"],
):
    agent.to_cli_sync(deps=deps)
