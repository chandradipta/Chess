import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.db import engine
from app.models import Base

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    return asyncio.get_event_loop()

@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_signup_login_create_game_and_pgn():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signup", json={"username":"testuser","email":"t@example.com","password":"password"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        r2 = await client.post("/games", json={"ai": True, "ai_difficulty":"easy", "color":"white"}, headers=headers)
        assert r2.status_code == 200
        data = r2.json()
        assert data["ai"] is True
        assert data["ai_side"] in ("white", "black")
        game_id = data["game_id"]
        r3 = await client.get(f"/games/{game_id}/pgn")
        assert r3.status_code == 200
        assert "pgn" in r3.json()