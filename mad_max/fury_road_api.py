"""
Duchańska Ścieżka - FastAPI Server
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json

from fury_road_server import (
    start_game, move_to, attempt_escape, talk_to, buy_item,
    roll_encounter, combat, flee, next_day, check_survival,
    get_state, reset, get_tools, handle_tool
)

app = FastAPI(title="Fury Road MCP")


class ToolCall(BaseModel):
    name: str
    arguments: Optional[dict] = None


class GameStart(BaseModel):
    player_name: str
    character: Optional[str] = None


class MoveRequest(BaseModel):
    location: str


class TalkRequest(BaseModel):
    npc: str


class BuyRequest(BaseModel):
    item: str
    cost: int


class CombatRequest(BaseModel):
    enemy: str


@app.get("/")
def root():
    return {"status": "ok", "game": "Duchańska Ścieżka"}


@app.get("/v1/tools")
def list_tools():
    return {"tools": get_tools()}


@app.post("/v1/tools/call")
def call_tool(tool_call: ToolCall):
    result = handle_tool(tool_call.name, tool_call.arguments)
    return {"result": result}


@app.post("/game/start")
def game_start(request: GameStart):
    result = start_game(request.player_name, request.character)
    return {"output": result}


@app.post("/game/move")
def game_move(request: MoveRequest):
    result = move_to(request.location)
    return {"output": result}


@app.post("/game/escape")
def game_escape():
    result = attempt_escape()
    return {"output": result}


@app.post("/game/talk")
def game_talk(request: TalkRequest):
    result = talk_to(request.npc)
    return {"output": result}


@app.post("/game/combat")
def game_combat(request: CombatRequest):
    result = combat(request.enemy)
    return {"output": result}


@app.get("/game/survival")
def game_survival():
    result = check_survival()
    return {"output": result}


@app.get("/game/state")
def game_state():
    result = get_state()
    return {"output": result}


@app.post("/game/reset")
def game_reset():
    result = reset()
    return {"output": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1313)
