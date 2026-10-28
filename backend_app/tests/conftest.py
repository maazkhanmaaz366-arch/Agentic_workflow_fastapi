import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url = "http://test") as act:
        yield act