import os

import pytest
from app import config
from app.db import get_session, override_engine
from app.main import create_app
from httpx import AsyncClient
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture(scope="module", autouse=True)
def test_settings():
    config.get_settings.cache_clear()
    os.environ["PPTO_DATABASE_URL"] = "sqlite://"
    return config.get_settings()


@pytest.fixture
async def app_client(test_settings):
    engine = create_engine(test_settings.database_url, connect_args={"check_same_thread": False})
    override_engine(engine)
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = get_test_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_and_get_entry(app_client):
    payload = {
        "fecha": "2025-01-01",
        "win_tgm": 1000,
        "coin_in": 5000,
        "win_mesas": 200,
        "drop_mesas": 300,
        "nota": "Inicial",
    }

    create_response = await app_client.post("/entries/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] > 0
    assert created["coin_in"] == payload["coin_in"]

    get_response = await app_client.get(f"/entries/{created['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == created["id"]


@pytest.mark.asyncio
async def test_filters_and_update(app_client):
    payload = {
        "fecha": "2025-02-01",
        "win_tgm": 1500,
        "coin_in": 7500,
        "win_mesas": 500,
        "drop_mesas": 650,
        "nota": "Filtro",
    }
    await app_client.post("/entries/", json=payload)

    list_response = await app_client.get("/entries/?start_date=2025-02-01&min_coin_in=7000")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 1
    assert data["items"][0]["coin_in"] == payload["coin_in"]

    entry_id = data["items"][0]["id"]
    update_response = await app_client.put(
        f"/entries/{entry_id}", json={"nota": "Actualizado", "coin_in": 8000}
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["nota"] == "Actualizado"
    assert updated["coin_in"] == 8000

    delete_response = await app_client.delete(f"/entries/{entry_id}")
    assert delete_response.status_code == 204

    missing = await app_client.get(f"/entries/{entry_id}")
    assert missing.status_code == 404
