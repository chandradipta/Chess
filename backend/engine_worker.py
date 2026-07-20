"""
Engine worker — consumes Redis list `ai_jobs`, computes AI move(s) and publishes results to `ai_results`.
"""
import os
import json
import time
import redis
from app.stockfish_utils import get_bestmoves_for_difficulty

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
AI_JOBS = "ai_jobs"
AI_RESULTS_CHANNEL = "ai_results"

def main():
    r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
    print("Engine worker started, waiting for jobs...")
    while True:
        try:
            item = r.brpop(AI_JOBS, timeout=5)
            if not item:
                continue
            _, raw = item
            job = json.loads(raw)
            game_id = job.get("game_id")
            fen = job.get("fen")
            difficulty = job.get("difficulty", "medium")
            try:
                moves = get_bestmoves_for_difficulty(fen, difficulty=difficulty, multipv=1)
                if moves and "move" in moves[0]:
                    move = moves[0]["move"]
                    payload = {"game_id": game_id, "move": move, "by_ai": True}
                    r.publish(AI_RESULTS_CHANNEL, json.dumps(payload))
                else:
                    payload = {"game_id": game_id, "error": "no_move"}
                    r.publish(AI_RESULTS_CHANNEL, json.dumps(payload))
            except Exception as e:
                payload = {"game_id": game_id, "error": "engine_error", "message": str(e)}
                r.publish(AI_RESULTS_CHANNEL, json.dumps(payload))
        except Exception as e:
            print("Worker error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()