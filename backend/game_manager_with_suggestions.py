# Note: this is an add-on to the previously shown GameManager / GameSession.
# Requires: python-chess (pip install chess), Stockfish binary available, FastAPI websockets already wired.

import asyncio
import time
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
import chess
import chess.engine
import concurrent.futures

STOCKFISH_PATH = "/usr/bin/stockfish"  # adjust for your environment
SUGGESTION_TIMEOUT = 90.0  # seconds
MULTIPV = 3
ENGINE_DEPTH = 15
ENGINE_MOVETIME_MS = None  # or set movetime in ms instead of depth

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

class GameSession:
    def __init__(self, game_id: str, ai_side: Optional[str] = None):
        self.game_id = game_id
        self.board = chess.Board()
        self.sockets: Set[WebSocket] = set()  # all sockets (players + spectators)
        self.player_sockets: Dict[str, WebSocket] = {}  # 'white' -> ws, 'black' -> ws (if present)
        self.lock = asyncio.Lock()
        self.last_activity_ts = time.time()
        self.inactivity_task: Optional[asyncio.Task] = None
        self.ai_side = ai_side  # 'white' or 'black' if one side is AI, else None
        self._engine = None

    async def start_inactivity_watcher(self):
        # start a background task (idempotent)
        if self.inactivity_task is None or self.inactivity_task.done():
            self.inactivity_task = asyncio.create_task(self._inactivity_loop())

    async def _inactivity_loop(self):
        try:
            while True:
                await asyncio.sleep(5)  # poll interval
                # Only consider suggestions when this session has an AI opponent
                if not self.ai_side:
                    continue
                # determine which color is to move
                color_to_move = 'white' if self.board.turn == chess.WHITE else 'black'
                # only suggest if the human player is the side to move
                if color_to_move == self.ai_side:
                    continue  # it's AI's move, no hint to human currently
                # check inactivity
                idle = time.time() - self.last_activity_ts
                if idle >= SUGGESTION_TIMEOUT:
                    # ensure we only send once per idle period; update timestamp to avoid repeated suggestions
                    self.last_activity_ts = time.time()
                    # compute suggestions (run in thread executor to avoid blocking)
                    suggestions = await asyncio.get_event_loop().run_in_executor(
                        _executor, self._compute_suggestions, self.board.fen(), MULTIPV, ENGINE_DEPTH, ENGINE_MOVETIME_MS
                    )
                    # send only to the player whose turn it is (the human)
                    target_ws = self.player_sockets.get(color_to_move)
                    if target_ws:
                        try:
                            await target_ws.send_json({"type": "suggestions", "suggestions": suggestions})
                        except Exception:
                            # handle broken socket; remove if needed
                            pass
                # continue loop
        except asyncio.CancelledError:
            return

    def _compute_suggestions(self, fen: str, multipv: int, depth: int, movetime_ms: Optional[int]):
        # Synchronous blocking engine interaction (safely run in thread)
        suggestions = []
        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                # set MultiPV
                try:
                    engine.configure({"MultiPV": multipv})
                except Exception:
                    # Some versions may differ; ignore if not supported
                    pass
                engine.position(chess.Board(fen))
                if movetime_ms:
                    info = engine.analysis(chess.Board(fen), limit=chess.engine.Limit(time=movetime_ms / 1000.0), multipv=multipv)
                else:
                    info = engine.analysis(chess.Board(fen), limit=chess.engine.Limit(depth=depth), multipv=multipv)
                # 'info' is a generator that yields info dicts; collect last complete set of PVs
                # Simpler approach: call engine.analyse which returns dict for single PV; for multipv we iterate
                # Use engine.play repeatedly by setting MultiPV and parsing info lines:
                # For reliability we will call engine.analyse multiple times with different PV indices if needed.
                # The python-chess engine API returns Score objects in info.
                # Instead we'll use engine.analysis generator and gather candidate infos as they come.
                pv_infos = []
                # read several info updates until we have PV info entries
                for entry in info:
                    # entry is dict-like containing 'pv' and 'score' sometimes
                    if "pv" in entry and "score" in entry:
                        pv_infos.append(entry)
                    # break when we have at least multipv distinct PVs
                    # Note: multiple entries will be yielded; rely on engine implementation
                # if pv_infos empty fallback to engine.go bestmove
                if not pv_infos:
                    # fallback: ask bestmove
                    res = engine.play(chess.Board(fen), chess.engine.Limit(depth=depth))
                    best = res.move.uci()
                    suggestions = [{"move": best, "score": None, "pv": [best]}]
                else:
                    # parse pv_infos into structured suggestions
                    # Keep up to `multipv` unique PVs
                    seen = set()
                    for info_entry in pv_infos:
                        pv = [m.uci() for m in info_entry.get("pv", [])]
                        if not pv:
                            continue
                        move = pv[0]
                        if move in seen:
                            continue
                        seen.add(move)
                        score = info_entry.get("score")
                        # convert score to a human-friendly representation
                        if isinstance(score, chess.engine.PovScore):
                            # PovScore contains mate or cp
                            s = score.white() if True else score
                            # attempt to get centipawns or mate
                            if s.is_mate():
                                val = {"mate": s.mate()}
                            else:
                                val = {"cp": s.score()}
                        else:
                            val = None
                        suggestions.append({"move": move, "score": val, "pv": pv})
                        if len(suggestions) >= multipv:
                            break
        except Exception as e:
            # log error in real app
            return [{"error": "engine_error", "message": str(e)}]
        return suggestions

    # Call this whenever a player sends a move or interacts (resets inactivity timer)
    def mark_activity(self):
        self.last_activity_ts = time.time()

# Example usage inside GameManager.handle_move:
# after accepting and pushing a move:
# sess.mark_activity()
# ensure watcher is running:
# await sess.start_inactivity_watcher()