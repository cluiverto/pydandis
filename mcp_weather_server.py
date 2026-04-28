# mcp_weather_server_http.py
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn

mcp = FastMCP("weather-server-http")

@mcp.tool()
def weather(city: str) -> str:
    """Get weather for a city."""
    dummy_temps = {
        "nyc": "58°F", "london": "48°F", "san francisco": "62°F"
    }
    temp = dummy_temps.get(city.lower(), "65°F (approx)")
    return f"The current temperature in {city.title()} is {temp}."

# FastAPI wrapper żeby działał na porcie 8000
app = FastAPI(title="Weather MCP Server")

@app.get("/")
def root():
    return {"status": "MCP server running", "endpoint": "/mcp"}

if __name__ == "__main__":
    # Uruchomimy MCP + FastAPI
    import threading
    from mcp.server.sse import SseServerTransport
    from starlette.routing import Route
    from starlette.applications import Starlette
    
    # MCP SSE endpoint
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request.send) as (read, write):
            await mcp._mcp_server.run(
                read,
                write,
                mcp._mcp_server.create_initialization_options()
            )
    
    # Starlette app for SSE
    sse_app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=sse.handle_post_message),
    ])
    
    # Run both
    print("Starting MCP SSE server on http://localhost:9999/sse")
    uvicorn.run(sse_app, host="0.0.0.0", port=8000)
