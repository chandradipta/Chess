class GameSession:
    def __init__(self, game_id: str, ai_side: Optional[str] = None, ai_difficulty: str = "medium"):
        self.game_id = game_id
        self.board = chess.Board()
        self.ai_side = ai_side  # 'white'|'black' or None
        self.ai_difficulty = ai_difficulty
        self.player_sockets = {}
        self.sockets = set()
        self.last_activity_ts = time.time()
        self.inactivity_task = None
        # ...

    async def handle_ai_move(self):
        # called when it's AI's turn
        suggestions = get_bestmove_for_difficulty(self.board.fen(), difficulty=self.ai_difficulty, multipv=1)
        if suggestions and "move" in suggestions[0]:
            uci = suggestions[0]["move"]
            move = chess.Move.from_uci(uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                msg = {"type": "move", "uci": uci, "fen": self.board.fen()}
                await self.broadcast(msg)
                self.mark_activity()
                # persist move to DB etc.