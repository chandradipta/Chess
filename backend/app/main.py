import os
import asyncio
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from routes import users, games
from game_manager import game_manager
from utils import decode_access_token
import aioredis

app = FastAPI(title="Chess App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/auth", tags=["auth"])
app.include_router(games.router, prefix="/games", tags=["games"])

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")

@app.on_event("startup")
async def startup():
    app.state.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    asyncio.create_task(game_manager.start_ai_result_listener(app.state.redis))
    await game_manager.start_background_tasks()

@app.on_event("shutdown")
async def shutdown():
    try:
        await app.state.redis.close()
    except Exception:
        pass
    await game_manager.shutdown()

@app.websocket("/ws/games/{game_id}")
async def ws_game(websocket: WebSocket, game_id: int, token: str = Query(None)):
    user_id = None
    if token:
        user_id = decode_access_token(token)
        if user_id is None:
            await websocket.close(code=1008)
            return
    await game_manager.handle_ws(game_id=game_id, websocket=websocket, user_id=int(user_id) if user_id else None)