from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from db import Base
import enum

class GameStatus(str, enum.Enum):
    waiting = "waiting"
    active = "active"
    finished = "finished"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    rating = Column(Integer, default=1200)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    white_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    black_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    fen = Column(String(1000), default="startpos")
    pgn = Column(Text, default="")
    status = Column(Enum(GameStatus), default=GameStatus.waiting)
    time_control = Column(String(50), default="5+0")
    ai = Column(String(5), default="false")
    ai_side = Column(String(10), nullable=True)
    ai_difficulty = Column(String(20), default="medium")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Move(Base):
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    uci = Column(String(16), nullable=False)
    san = Column(String(64), nullable=True)
    turn_number = Column(Integer, nullable=False)
    clock_white_ms = Column(Integer, nullable=True)
    clock_black_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())