import os, sys, httpx, json, re
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

from lyricsgenius import Genius

from langfuse import get_client, propagate_attributes

Agent.instrument_all()

genius = Genius(os.getenv("GENIUS_ACCESS_TOKEN"))
server = MCPServerStreamableHTTP(os.getenv("ALPHAVANTAGE_URL"))

# ── Existing tools ───────────────────────────────────────


async def add_italian_word(
    ctx: RunContext[DeepAgentDeps], word: str, translation: str
) -> str:
    """Add a word to the Italian vocabulary list (saved as JSON)."""
    vocab_path = "italian_vocab.json"
    try:
        content = await ctx.deps.backend.read_file(vocab_path)
        vocab = json.loads(content)
    except:
        vocab = []
    vocab.append({"word": word, "translation": translation})
    await ctx.deps.backend.write_file(
        vocab_path, json.dumps(vocab, indent=2, ensure_ascii=False)
    )
    return f"Added: {word} = {translation} (saved to {vocab_path})"


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


# ── Song tools ───────────────────────────────────────────


async def search_italian_songs(ctx: RunContext[DeepAgentDeps], query: str) -> str:
    """Search for Italian songs on Genius by title, artist, or keyword. Returns a formatted list of matching songs."""
    try:
        results = genius.search_songs(query, per_page=8)
        if not results or "hits" not in results or not results["hits"]:
            return "Nessuna canzone trovata."
        lines = []
        for hit in results["hits"]:
            s = hit["result"]
            artist = s["primary_artist"]["name"]
            title = s["title"]
            year = s.get("release_date_components", {})
            year_str = str(year.get("year", "")) if year else ""
            lines.append(f"- {title} — {artist} {year_str}")
        return "Canzoni trovate:\n" + "\n".join(lines)
    except Exception as e:
        return f"Errore nella ricerca: {e}"


async def get_song_lyrics(
    ctx: RunContext[DeepAgentDeps], title: str, artist: str = ""
) -> str:
    """Fetch full lyrics of a song from Genius. Provide title and optionally artist."""
    try:
        song = genius.search_song(title, artist)
        if not song:
            return f"Canzone '{title}' di {artist} non trovata."
        lyrics = song.lyrics
        lyrics_clean = re.sub(r"[0-9]+Embed$", "", lyrics, flags=re.MULTILINE)
        lyrics_clean = re.sub(
            r"^[0-9]+Contributors.*$", "", lyrics_clean, flags=re.MULTILINE
        )
        lyrics_clean = lyrics_clean.strip()
        return f"Testo di '{song.full_title or song.title}' — {song.artist}:\n\n{lyrics_clean}"
    except Exception as e:
        return f"Errore nel caricamento del testo: {e}"


# ── Agent ────────────────────────────────────────────────

instructions = """Sei un assistente per imparare l'italiano attraverso le canzoni.

Regole:
- Rispondi sempre in italiano.
- Usa search_italian_songs per cercare canzoni su Genius.
- Usa get_song_lyrics per ottenere il testo completo di una canzone.
- Dopo aver mostrato il testo, offri sempre: traduzione, esercizi, e vocabolario.
- Esercizi che puoi generare: cloze (riempi gli spazi), abbina frasi, domande di comprensione, quiz di vocabolario, ordina i versi.
- Usa add_italian_word per salvare nuove parole nel vocabolario.
- Quando cerchi canzoni, dai priorità ad artisti italiani (Bocelli, Pausini, Ramazzotti, Måneskin, Zucchero, Battisti, De André, etc.).
"""

agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions=instructions,
    include_todo=True,
    toolsets=[server],
    skill_directories=["skills"],
    instrument=True,
)

# Register new song tools (existing tools like add_italian_word
# are already registered by the skills system from SKILL.md)
wrapped = agent.wrapped if hasattr(agent, "wrapped") else agent
wrapped.tool(search_italian_songs)
wrapped.tool(get_song_lyrics)

deps = DeepAgentDeps(backend=LocalBackend("."))
langfuse = get_client()

with propagate_attributes(
    user_id="deep-user",
    session_id="deep-session",
    tags=["deep-agent"],
):
    agent.to_cli_sync(deps=deps)
