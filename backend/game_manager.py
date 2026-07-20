import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
import chess
import chess.pgn
from stockfish_utils import StockfishEngine

class GameSession:
    def __init__(self, game_id):
        self.game_id = game_id
        self.board = chess.Board()
        self.sockets: Set[WebSocket] = set()
        self.lock = asyncio.Lock()
        # clocks, players, status, move history, etc.

class GameManager:
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.stockfish = StockfishEngine(path="/usr/bin/stockfish")

    async def handle_connection(self, game_id: str, websocket: WebSocket, token: str):
        sess = self.sessions.setdefault(game_id, GameSession(game_id))
        sess.sockets.add(websocket)
        # send initial state
        await websocket.send_json({"type":"sync", "fen": sess.board.fen(), "moves":[]})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg["type"] == "move":
                await self.handle_move(sess, websocket, msg)
            elif msg["type"] == "ai_move":
                await self.handle_ai_move(sess)
            # other message types...

    async def handle_move(self, sess: GameSession, websocket: WebSocket, msg):
        async with sess.lock:
            uci = msg.get("uci") or f"{msg['from']}{msg['to']}{msg.get('promotion','')}"
            try:
                move = chess.Move.from_uci(uci)
            except Exception:
                await websocket.send_json({"type":"error","reason":"invalid_uci"})
                return
            if move not in sess.board.legal_moves:
                await websocket.send_json({"type":"error","reason":"illegal_move"})
                return
            sess.board.push(move)
            # persist move to DB (async)
            out = {"type":"move","uci":move.uci(),"san":sess.board.peek().san if hasattr(sess.board,'peek') else None, "fen":sess.board.fen()}
            await self.broadcast(sess, out)

    async def handle_ai_move(self, sess: GameSession):
        # use stockfish to get best move
        best = self.stockfish.get_bestmove(sess.board.fen())
        move = chess.Move.from_uci(best)
        sess.board.push(move)
        await self.broadcast(sess, {"type":"move","uci":move.uci(),"fen":sess.board.fen()})

    async def broadcast(self, sess: GameSession, message: dict):
        websockets = list(sess.sockets)
        for ws in websockets:
            try:
                await ws.send_json(message)
            except:
                sess.sockets.remove(ws)

    async def disconnect(self, game_id: str, websocket: WebSocket):
        sess = self.sessions.get(game_id)
        if sess and websocket in sess.sockets:
            sess.sockets.remove(websocket)