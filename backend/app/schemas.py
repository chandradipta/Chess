from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class GameCreate(BaseModel):
    ai: bool = False
    ai_difficulty: Optional[str] = "medium"
    color: Optional[str] = "random"
    time_control: Optional[str] = "5+0"