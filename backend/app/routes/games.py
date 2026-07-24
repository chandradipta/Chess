from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select as sa_select
import chess
import chess.pgn

from ..schemas import GameCreate
from ..db import AsyncSessionLocal
from ..models import Game, Move
from ..game_manager import game_manager
from ..utils import get_current_user_optional

router = APIRouter()


class GameOut(BaseModel):
    game_id: int
    ai: bool
    ai_side: str = None
    ai_difficulty: str = None
    white_id: int = None
    black_id: int = None


@router.post("/", summary="Create a game", response_model=GameOut)
async def create_game(
    payload: GameCreate,
    current_user=Depends(get_current_user_optional),
):
    async with AsyncSessionLocal() as session:
        game = Game(
            ai="true" if payload.ai else "false",
            ai_side=None,
            ai_difficulty=payload.ai_difficulty or "medium",
            time_control=payload.time_control or "5+0",
        )

        if payload.ai:
            if payload.color == "white":
                game.ai_side = "black"
            elif payload.color == "black":
                game.ai_side = "white"
            else:
                import random
                game.ai_side = random.choice(["white", "black"])

        if current_user:
            if payload.ai:
                if game.ai_side == "white":
                    game.black_id = current_user.id
                else:
                    game.white_id = current_user.id
            else:
                if payload.color == "white":
                    game.white_id = current_user.id
                elif payload.color == "black":
                    game.black_id = current_user.id
                else:
                    game.white_id = current_user.id

        session.add(game)
        await session.commit()
        await session.refresh(game)

        await game_manager.create_session_from_db(
            game.id,
            ai_side=game.ai_side,
            ai_difficulty=game.ai_difficulty,
        )

        return GameOut(
            game_id=game.id,
            ai=(game.ai == "true"),
            ai_side=game.ai_side,
            ai_difficulty=game.ai_difficulty,
            white_id=game.white_id,
            black_id=game.black_id,
        )


@router.get("/{game_id}/pgn", summary="Get PGN for a game")
async def get_game_pgn(game_id: int):
    async with AsyncSessionLocal() as session:
        q = await session.execute(
            sa_select(Game).filter(Game.id == game_id)
        )

        game = q.scalars().first()

        if not game:
            raise HTTPException(
                status_code=404,
                detail="game not found",
            )

        q2 = await session.execute(
            sa_select(Move)
            .filter(Move.game_id == game_id)
            .order_by(Move.id)
        )

        moves = q2.scalars().all()

        pgn_game = chess.pgn.Game()
        node = pgn_game
        board = chess.Board()

        for mv in moves:
            try:
                move = chess.Move.from_uci(mv.uci)
                node = node.add_variation(move)
                board.push(move)
            except Exception:
                pass

        return {
            "pgn": str(pgn_game),
        }