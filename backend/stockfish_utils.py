import chess
import chess.engine
from typing import Optional, Dict, Any

STOCKFISH_PATH = "/usr/bin/stockfish"  # adjust

def _configure_engine(engine: chess.engine.SimpleEngine, options: Dict[str, Any]):
    # Try to configure engine options; ignore failures for unsupported options
    for k, v in (options or {}).items():
        try:
            engine.configure({k: v})
        except Exception:
            # Option might not be supported by the engine binary; ignore it
            pass

def get_bestmove_for_difficulty(fen: str, difficulty: str = "medium", multipv: int = 1):
    settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS["medium"])
    depth = settings.get("depth")
    movetime_ms = settings.get("movetime_ms")
    uci_opts = settings.get("uci_options", {})

    board = chess.Board(fen)
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            # configure UCI options when possible
            _configure_engine(engine, uci_opts)
            # configure MultiPV if we want multiple lines
            if multipv and multipv > 1:
                try:
                    engine.configure({"MultiPV": multipv})
                except Exception:
                    pass

            # prefer movetime if provided, otherwise depth
            if movetime_ms:
                limit = chess.engine.Limit(time=movetime_ms / 1000.0)
            else:
                limit = chess.engine.Limit(depth=depth)

            # Use analysis to get multipv or play for single best move
            if multipv and multipv > 1:
                # engine.analysis yields updates; collect final PVs
                pv_list = []
                # We'll iterate a limited number of info updates and extract PVs
                info_gen = engine.analysis(board, limit=limit, multipv=multipv)
                for info in info_gen:
                    if "pv" in info and "score" in info:
                        pv = [m.uci() for m in info.get("pv", [])]
                        score = info.get("score")
                        pv_list.append({"pv": pv, "score": score})
                    # The generator yields many entries; we'll collect until we have multipv unique first-moves
                    # For robustness, break if we have at least multipv entries
                    if len(pv_list) >= multipv:
                        break
                # fallback: if none found use engine.play()
                if not pv_list:
                    res = engine.play(board, limit=limit)
                    return [{"move": res.move.uci(), "pv": [res.move.uci()], "score": None}]
                # return structured moves
                suggestions = []
                seen_moves = set()
                for e in pv_list:
                    if not e.get("pv"):
                        continue
                    move = e["pv"][0]
                    if move in seen_moves:
                        continue
                    seen_moves.add(move)
                    # convert score to friendly format
                    score = None
                    s = e.get("score")
                    try:
                        if hasattr(s, "white"):
                            ps = s.white()
                            if ps.is_mate():
                                score = {"mate": ps.mate()}
                            else:
                                score = {"cp": ps.score()}
                    except Exception:
                        score = None
                    suggestions.append({"move": move, "pv": e["pv"], "score": score})
                return suggestions[:multipv]
            else:
                # single best move
                res = engine.play(board, limit=limit)
                return [{"move": res.move.uci(), "pv": [res.move.uci()], "score": None}]
    except Exception as e:
        # handle engine failure gracefully
        return [{"error": "engine_error", "message": str(e)}]