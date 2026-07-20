from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from db import AsyncSessionLocal
from models import User
from schemas import UserCreate, Token
from utils import get_password_hash, verify_password, create_access_token
from fastapi import status

router = APIRouter()

@router.post("/signup", response_model=Token)
async def signup(payload: UserCreate):
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(User).filter((User.username==payload.username) | (User.email==payload.email)))
        existing = q.scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="username or email already exists")
        u = User(username=payload.username, email=payload.email, password_hash=get_password_hash(payload.password))
        session.add(u)
        await session.commit()
        await session.refresh(u)
        token = create_access_token(str(u.id))
        return {"access_token": token}

@router.post("/login", response_model=Token)
async def login(payload: UserCreate):
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(User).filter(User.username==payload.username))
        user = q.scalars().first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(str(user.id))
        return {"access_token": token}