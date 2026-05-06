import os, sys, httpx, json
from dotenv import load_dotenv
load_dotenv()

bam_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, bam_dir)
from config import get_openrouter_model

from pydantic_ai import Agent, RunContext
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend, LocalBackend
from pydantic_ai.capabilities import MCP  

from pydantic_ai import PrefixedToolset, FunctionToolset
from pydantic_ai.mcp import MCPServerStreamableHTTP




from langfuse import get_client, propagate_attributes

#langfuse (init)
Agent.instrument_all()


server = MCPServerStreamableHTTP(os.getenv("ALPHAVANTAGE_URL"))

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

#tool
async def wiki_lookup_italian(ctx: RunContext[DeepAgentDeps], word: str) -> str:
    """Look up an Italian word on Italian Wikipedia (no API key needed)."""
    try:
        resp = await httpx.AsyncClient().get(
            f"https://it.wikipedia.org/w/api.php?action=query&titles={word}&prop=extracts&exintro&format=json&explaintext"
        )
        data = resp.json()
        page = next(iter(data["query"]["pages"].values()))
        if "extract" in page:
            return f"Definizione di {word}: {page['extract'][:500]}"
        return f"Parola {word} non trovata su Wikipedia."
    except:
        return "Errore nel recupero dei dati."


#agent
agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions='''You always respond in Italian.''',
    include_todo=True,
    toolsets=[server],
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
