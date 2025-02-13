import asyncio
import logging
from typing import AsyncGenerator, Generator

import asyncpg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app.core.db.database import Base, async_get_db
from src.app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Ensure pytest-asyncio runs with a proper event loop."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def docker_postgres(docker_services) -> str:
    """Starts a PostgreSQL container for testing using pytest-docker."""
    port = docker_services.port_for("postgres", 5432)

    # ✅ Change DSN to `postgres://` instead of `postgresql+asyncpg://`
    db_url = f"postgres://testuser:testpassword@localhost:{port}/testdb"

    # Wait until the database is responsive
    docker_services.wait_until_responsive(
        timeout=30.0,  # Wait up to 30 seconds for PostgreSQL to start
        pause=2.0,  # Wait 2 seconds between retries
        check=lambda: asyncio.run(check_postgres_ready(db_url)),
    )

    return db_url


async def check_postgres_ready(db_url: str) -> bool:
    """Check if PostgreSQL is ready by attempting a connection."""

    # ✅ Ensure DSN uses `postgresql://`
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        conn = await asyncpg.connect(db_url, timeout=2)  # 2s timeout per attempt
        await conn.close()
        logging.info("✅ PostgreSQL is ready!")
        return True
    except Exception as e:
        logging.warning(f"⏳ PostgreSQL is not ready yet: {e}")
        return False


async def wait_for_db_ready(db_url: str, retries: int = 10, delay: float = 2.0) -> None:
    """Wait until the test database is ready before running tests."""
    for attempt in range(retries):
        if await check_postgres_ready(db_url):
            logging.info(f"✅ Database is ready after {attempt + 1} attempts")
            return
        logging.warning(f"⏳ Waiting for database... Attempt {attempt + 1}/{retries}")
        await asyncio.sleep(delay)

    raise RuntimeError("❌ Test database did not become available in time.")


@pytest.fixture(scope="session")
async def test_db(
    docker_postgres: str,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Creates a new test database with SQLAlchemy, applying schema migrations."""

    # ✅ Replace `postgresql+asyncpg://` with `postgresql://`
    sqlalchemy_db_url = docker_postgres.replace("postgres://", "postgresql+asyncpg://")

    await wait_for_db_ready(docker_postgres)  # Ensure DB is up

    test_engine = create_async_engine(sqlalchemy_db_url, echo=False, future=True)
    testing_session_local = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield testing_session_local

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def override_get_db(
    test_db: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Override the FastAPI database dependency to use the test database session."""
    async with test_db() as session:
        yield session


@pytest.fixture(scope="function")
def client(override_get_db) -> TestClient:
    """Create a FastAPI TestClient instance with an overridden database dependency."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with override_get_db as session:
            yield session  # ✅ Correctly yielding session as async generator

    app.dependency_overrides[async_get_db] = _override_get_db
    return TestClient(app)
