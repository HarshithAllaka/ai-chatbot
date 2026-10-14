import pytest
from httpx import ASGITransport, AsyncClient

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base import Base
from app.db.database import get_db
from app.main import app

TEST_ENGINE = create_async_engine(
    settings.database_test_url,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    TEST_ENGINE,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


from sqlalchemy import text

@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    try:
        async with TEST_ENGINE.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        # DB not reachable during standalone unit tests; proceed gracefully
        pass

    yield

    try:
        async with TEST_ENGINE.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass



@pytest.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client