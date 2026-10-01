import os

os.environ.setdefault("APP_DATABASE_URL", "postgresql+psycopg://design:design@localhost:5432/design_test")
os.environ["APP_LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.rag.retriever import seed_knowledge  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    init_db()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        seed_knowledge(s)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
