import os
import chess
import chess.engine
from typing import Dict, Any

from .ai_difficulty import DIFFICULTY_SETTINGS

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "/usr/local/bin/stockfish")


def _configure_engine(engine: chess.engine.SimpleEngine, options: Dict[str, Any]):
    for k, v in (options or {}).items():
        try:
            engine.configure({k: v})
        except Exception:
            pass


def get_bestmoves_for_difficulty(fen: str, difficulty: str = "medium", multipv: int = 1):
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS["medium"])
    depth = settings.get("depth")
    movetime_ms = settings.get("movetime_ms")
    uci_opts = settings.get("uci_options", {})

    board = chess.Board() if fen == "startpos" else chess.Board(fen)

    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            _configure_engine(engine, uci_opts)

            if multipv and multipv > 1:
                try:
                    engine.configure({"MultiPV": multipv})
                except Exception:
                    pass

            limit = (
                chess.engine.Limit(time=movetime_ms / 1000.0)
                if movetime_ms
                else chess.engine.Limit(depth=depth)
            )

            if multipv and multipv > 1:
                pv_list = []
                info_gen = engine.analysis(board, limit=limit, multipv=multipv)

                for info in info_gen:
                    if "pv" in info and "score" in info:
                        pv = [m.uci() for m in info.get("pv", [])]
                        score = info.get("score")
                        pv_list.append({"pv": pv, "score": score})

                        if len(pv_list) >= multipv:
                            break

                if not pv_list:
                    res = engine.play(board, limit=limit)
                    return [{
                        "move": res.move.uci(),
                        "pv": [res.move.uci()],
                        "score": None
                    }]

                suggestions = []
                seen = set()

                for e in pv_list:
                    pv = e.get("pv", [])

                    if not pv:
                        continue

                    move = pv[0]

                    if move in seen:
                        continue

                    seen.add(move)

                    s = e.get("score")
                    val = None

                    try:
                        ps = s.white()

                        if ps.is_mate():
                            val = {"mate": ps.mate()}
                        else:
                            val = {"cp": ps.score()}

                    except Exception:
                        val = None

                    suggestions.append({
                        "move": move,
                        "pv": pv,
                        "score": val
                    })

                return suggestions[:multipv]

            else:
                res = engine.play(board, limit=limit)

                return [{
                    "move": res.move.uci(),
                    "pv": [res.move.uci()],
                    "score": None
                }]

    except Exception as e:
        return [{
            "error": "engine_error",
            "message": str(e)
        }]