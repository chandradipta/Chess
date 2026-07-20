import asyncio
import time
import json
from typing import Dict, Set, Optional
import chess
from fastapi import WebSocket
from stockfish_utils import get_bestmoves_for_difficulty
import os
from db import AsyncSessionLocal
from models import Move, Game
from sqlalchemy import select
import aioredis

SUGGESTION_TIMEOUT = int(os.environ.get("SUGGESTION_TIMEOUT", "90"))
MULTIPV = 3
REDIS_AI_JOBS = "ai_jobs"
REDIS_AI_RESULTS_CHANNEL = "ai_results"

class GameSession:
    def __init__(self, game_id: int, ai_side: Optional[str] = None, ai_difficulty: str = "medium"):
        self.game_id = game_id
        self.board = chess.Board()
        self.sockets: Set[WebSocket] = set()
        self.player_sockets: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self.last_activity_ts = time.time()
        self.inactivity_task: Optional[asyncio.Task] = None
        self.ai_side = ai_side
        self.ai_difficulty = ai_difficulty
        self.closed = False
        self.turn_number = 0

    async def start_inactivity_watcher(self):
        if self.inactivity_task is None or self.inactivity_task.done():
            self.inactivity_task = asyncio.create_task(self._inactivity_loop())

    async def _inactivity_loop(self):
        try:
            while not self.closed:
                await asyncio.sleep(5)
                if not self.ai_side:
                    continue
                color_to_move = 'white' if self.board.turn == chess.WHITE else 'black'
                if color_to_move == self.ai_side:
                    continue
                idle = time.time() - self.last_activity_ts
                if idle >= SUGGESTION_TIMEOUT:
                    self.last_activity_ts = time.time()
                    suggestions = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: get_bestmoves_for_difficulty(self.board.fen(), difficulty=self.ai_difficulty, multipv=MULTIPV)
                    )
                    target_ws = self.player_sockets.get(color_to_move)
                    if target_ws:
                        try:
                            await target_ws.send_json({"type": "suggestions", "suggestions": suggestions})
                        except Exception:
                            pass
        except asyncio.CancelledError:
            return

    def mark_activity(self):
        self.last_activity_ts = time.time()

    async def broadcast(self, message: dict):
        websockets = list(self.sockets)
        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception:
                try:
                    self.sockets.remove(ws)
                except Exception:
                    pass

    async def close(self):
        self.closed = True
        if self.inactivity_task:
            self.inactivity_task.cancel()

class GameManager:
    def __init__(self):
        self.sessions: Dict[int, GameSession] = {}
        self._lock = asyncio.Lock()
        self.redis = None
        self._ai_result_task = None

    async def set_redis(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def start_ai_result_listener(self, redis_client: aioredis.Redis):
        await self.set_redis(redis_client)
        self._ai_result_task = asyncio.create_task(self._ai_result_loop(redis_client))

    async def _ai_result_loop(self, redis_client: aioredis.Redis):
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(REDIS_AI_RESULTS_CHANNEL)
        async for message in pubsub.listen():
            if message is None:
                await asyncio.sleep(0.01)
                continue
            if message.get("type") != "message":
                continue
            data = message.get("data")
            try:
                payload = json.loads(data)
            except Exception:
                continue
            game_id = int(payload.get("game_id"))
            uci = payload.get("move")
            sess = self.sessions.get(game_id)
            if not sess:
                continue
            await self._apply_ai_move(sess, uci)

    async def _apply_ai_move(self, sess: GameSession, uci: str):
        async with sess.lock:
            try:
                move = chess.Move.from_uci(uci)
            except Exception:
                return
            if move not in sess.board.legal_moves:
                return
            try:
                san = sess.board.san(move)
            except Exception:
                san = None
            sess.board.push(move)
            sess.turn_number += 1
            await sess.broadcast({"type": "move", "uci": move.uci(), "san": san, "fen": sess.board.fen(), "by_ai": True})
            await self._persist_move(session=sess, uci=move.uci(), san=san, user_id=None)

    async def create_session_from_db(self, game_id: int, ai_side: Optional[str] = None, ai_difficulty: str = "medium"):
        async with self._lock:
            sess = GameSession(game_id=game_id, ai_side=ai_side, ai_difficulty=ai_difficulty)
            self.sessions[game_id] = sess
            await sess.start_inactivity_watcher()
            return sess

    async def get_or_create_session(self, game_id: int, ai_side: Optional[str] = None, ai_difficulty: str = "medium"):
        async with self._lock:
            if game_id in self.sessions:
                return self.sessions[game_id]
            return await self.create_session_from_db(game_id, ai_side, ai_difficulty)

    async def handle_ws(self, game_id: int, websocket: WebSocket, user_id: Optional[int] = None):
        await websocket.accept()
        sess = await self.get_or_create_session(game_id)
        sess.sockets.add(websocket)
        await websocket.send_json({"type": "sync", "fen": sess.board.fen(), "game_id": game_id})
        await sess.start_inactivity_watcher()
        try:
            while True:
                text = await websocket.receive_text()
                data = json.loads(text)
                t = data.get("type")
                if t == "join":
                    color = data.get("color")
                    if color in ("white", "black"):
                        sess.player_sockets[color] = websocket
                    await websocket.send_json({"type":"joined","color":color})
                elif t == "move":
                    await self._handle_move(sess, websocket, data, user_id)
                elif t == "request_suggestions":
                    suggestions = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: get_bestmoves_for_difficulty(sess.board.fen(), difficulty=sess.ai_difficulty, multipv=MULTIPV)
                    )
                    await websocket.send_json({"type": "suggestions", "suggestions": suggestions})
                elif t == "mark_activity":
                    sess.mark_activity()
                elif t == "offer_draw" or t == "resign":
                    await sess.broadcast({"type": t, "by": user_id})
                elif t == "chat":
                    await sess.broadcast({"type": "chat", "from": user_id, "text": data.get("text", "")})
        except Exception:
            try:
                sess.sockets.remove(websocket)
            except Exception:
                pass

    async def _handle_move(self, sess: GameSession, websocket: WebSocket, msg: dict, user_id: Optional[int]):
        async with sess.lock:
            sess.mark_activity()
            uci = msg.get("uci")
            if not uci:
                await websocket.send_json({"type":"error","reason":"no_uci"})
                return
            try:
                move = chess.Move.from_uci(uci)
            except Exception:
                await websocket.send_json({"type":"error","reason":"invalid_uci"})
                return
            if move not in sess.board.legal_moves:
                await websocket.send_json({"type":"error","reason":"illegal_move"})
                return
            try:
                san = sess.board.san(move)
            except Exception:
                san = None
            sess.board.push(move)
            sess.turn_number += 1
            await sess.broadcast({"type":"move","uci": move.uci(), "san": san, "fen": sess.board.fen()})
            await self._persist_move(session=sess, uci=move.uci(), san=san, user_id=user_id)
            color_to_move = 'white' if sess.board.turn == chess.WHITE else 'black'
            if sess.ai_side == color_to_move:
                job = {"game_id": sess.game_id, "fen": sess.board.fen(), "difficulty": sess.ai_difficulty}
                if self.redis:
                    await self.redis.lpush(REDIS_AI_JOBS, json.dumps(job))
                else:
                    loop = asyncio.get_event_loop()
                    best = await loop.run_in_executor(None, lambda: get_bestmoves_for_difficulty(sess.board.fen(), difficulty=sess.ai_difficulty, multipv=1))
                    if best and "move" in best[0]:
                        ai_uci = best[0]["move"]
                        await self._apply_ai_move(sess, ai_uci)

    async def _persist_move(self, session: GameSession, uci: str, san: Optional[str], user_id: Optional[int]):
        async with AsyncSessionLocal() as db:
            m = Move(game_id=session.game_id, user_id=user_id, uci=uci, san=san, turn_number=session.turn_number)
            db.add(m)
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                return
            q = await db.execute(select(Move).filter(Move.game_id==session.game_id).order_by(Move.id))
            all_moves = q.scalars().all()
            import chess
            import chess.pgn
            pgn_game = chess.pgn.Game()
            node = pgn_game
            board = chess.Board()
            for mv in all_moves:
                try:
                    move_obj = chess.Move.from_uci(mv.uci)
                    node = node.add_variation(move_obj)
                    board.push(move_obj)
                except Exception:
                    pass
            qg = await db.execute(select(Game).filter(Game.id==session.game_id))
            g = qg.scalars().first()
            if g:
                g.pgn = str(pgn_game)
                db.add(g)
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()

    async def start_background_tasks(self):
        return

    async def shutdown(self):
        for s in list(self.sessions.values()):
            await s.close()

game_manager = GameManager()