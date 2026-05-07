import os, sys, httpx, json
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
from config import get_openrouter_model

from pydantic_ai import Agent, RunContext
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend, LocalBackend

from pydantic_ai.mcp import MCPServerStreamableHTTP

from langfuse import get_client, propagate_attributes

Agent.instrument_all()

server = MCPServerStreamableHTTP(os.getenv("ALPHAVANTAGE_URL"))

async def add_to_portfolio(ctx: RunContext[DeepAgentDeps], instrument: str, direction: str, entry_price: float, volume: int) -> str:
    """Add a simulated position to the demo portfolio."""
    path = "xtb_portfolio.json"
    try:
        content = await ctx.deps.backend.read_file(path)
        portfolio = json.loads(content)
    except:
        portfolio = {"positions": [], "cash": 100000}
    position = {"instrument": instrument, "direction": direction, "entry_price": entry_price, "volume": volume}
    portfolio["positions"].append(position)
    await ctx.deps.backend.write_file(path, json.dumps(portfolio, indent=2, ensure_ascii=False))
    return f"Added {direction.upper()} {volume}x {instrument} @ {entry_price}"

async def portfolio_summary(ctx: RunContext[DeepAgentDeps]) -> str:
    """Show current portfolio positions and cash balance."""
    path = "xtb_portfolio.json"
    try:
        content = await ctx.deps.backend.read_file(path)
        portfolio = json.loads(content)
    except:
        return "Portfolio is empty."
    lines = ['Cash: $' + f'{portfolio["cash"]:,.2f}']
    for p in portfolio['positions']:
        lines.append(f'{p["direction"].upper()} {p["volume"]}x {p["instrument"]} @ {p["entry_price"]}')
    return '\n'.join(lines)

async def market_price(ctx: RunContext[DeepAgentDeps], symbol: str) -> str:
    """Fetch current price for a symbol via public API."""
    try:
        resp = await httpx.AsyncClient().get(f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}')
        data = resp.json()
        meta = data['chart']['result'][0]['meta']
        price = meta['regularMarketPrice']
        prev = meta['chartPreviousClose']
        change = ((price - prev) / prev) * 100
        sign = '+' if change >= 0 else ''
        return f'{symbol}: ${price:.2f} ({sign}{change:.2f}%)'
    except Exception as e:
        return f'Could not fetch {symbol}: {e}'

async def fx_rate(ctx: RunContext[DeepAgentDeps], base: str, target: str) -> str:
    """Get current FX rate between two currencies."""
    pair = f'{base}{target}=X'
    try:
        resp = await httpx.AsyncClient().get(f'https://query1.finance.yahoo.com/v8/finance/chart/{pair}')
        data = resp.json()
        rate = data['chart']['result'][0]['meta']['regularMarketPrice']
        return f'{base}/{target}: {rate:.4f}'
    except:
        return f'Could not fetch rate for {base}/{target}.'

async def calculate_position_size(ctx: RunContext[DeepAgentDeps], capital: float, risk_pct: float, entry: float, stop: float) -> str:
    """Calculate position size based on account risk."""
    risk_amount = capital * (risk_pct / 100)
    risk_per_unit = abs(entry - stop)
    if risk_per_unit == 0:
        return 'Stop cannot equal entry price.'
    units = risk_amount / risk_per_unit
    total_value = units * entry
    return f'Capital: ${capital:,.0f} | Risk: {risk_pct}% (${risk_amount:,.0f}) | Units: {units:.2f} | Total: ${total_value:,.2f}'

instructions = """You are a Polish-speaking fintech assistant for XTB.
Help users with market research, portfolio tracking, and trading simulations.
Always respond in Polish.
Use tools to fetch market data, manage the demo portfolio, and calculate risk.
Be concise but informative -- like a real financial analyst."""

agent = create_deep_agent(
    model=get_openrouter_model(),
    instructions=instructions,
    include_todo=True,
    toolsets=[server],
    skill_directories=['skills'],
    instrument=True
)

deps = DeepAgentDeps(backend=LocalBackend('.'))
langfuse = get_client()

with propagate_attributes(
    user_id='xtb-user',
    session_id='xtb-session',
    tags=['xtb', 'fintech-agent'],
):
    agent.to_cli_sync(deps=deps)