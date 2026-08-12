import json
import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db, async_session_factory
from app.services.ai_service import AIProvider


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register():
    email = f"test-{uuid.uuid4().hex[:8]}@academia.ai"
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "full_name": "Test User",
            "password": "testpass123",
            "role": "student",
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_login():
    email = f"login-{uuid.uuid4().hex[:8]}@academia.ai"
    username = f"loginuser_{uuid.uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register_response = await client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "full_name": "Login Test User",
            "password": "testpass123",
            "role": "student",
        })
        assert register_response.status_code == 200

        response = await client.post("/api/auth/login", json={
            "email": email,
            "password": "testpass123",
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_generate_questions_fallback_when_ai_returns_invalid_data(monkeypatch):
    provider = AIProvider()

    async def fake_chat(messages, temperature=0.4, max_tokens=2048, stream=True, task="stem"):
        yield json.dumps({"role": "assistant", "content": "This is not valid JSON question data."})

    monkeypatch.setattr(provider, "chat", fake_chat)

    questions = await provider.generate_questions("Python loops are useful for repeated tasks.", count=3, difficulty="easy")

    assert len(questions) == 3
    for question in questions:
        assert question["question_text"]
        assert question["options"]
        assert question["correct_answer"]