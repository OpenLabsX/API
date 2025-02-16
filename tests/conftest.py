# conftest.py

import logging
import pytest

from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine  # <-- Sync engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.exc import SQLAlchemyError
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.core.db.database import Base, async_get_db

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture(scope="session")
def postgres_container() -> str:
    """
    1) Spin up a Postgres container once per session.
       Return an *async* connection URL (postgresql+asyncpg://...) for our app.
    """
    logger.info("Starting Postgres test container...")
    with PostgresContainer("postgres:17") as container:
        container.start()

        # E.g. "postgresql+psycopg2://postgres:postgres@localhost:5432/db"
        raw_url = container.get_connection_url()
        # Convert to async driver for the app
        async_url = raw_url.replace("psycopg2", "asyncpg")

        logger.info(f"Test container up => {async_url}")
        yield async_url

    logger.info("Postgres test container stopped.")


@pytest.fixture(scope="session", autouse=True)
def create_db_schema(postgres_container: str) -> None:
    """
    2) Use a *synchronous* engine to create all tables once at session start.
       This avoids bridging an async loop for table creation.

       We do *not* drop tables (the container is ephemeral anyway).
    """
    # Replace 'asyncpg' -> 'psycopg2' for the sync engine
    sync_url = postgres_container.replace("asyncpg", "psycopg2")
    logger.info(f"Creating schema with sync engine => {sync_url}")

    sync_engine = create_engine(sync_url, echo=False, future=True)

    try:
        Base.metadata.create_all(sync_engine)
        logger.info("All tables created (sync).")
    except SQLAlchemyError as err:
        logger.exception("Error creating tables.")
        raise err
    finally:
        sync_engine.dispose()
        logger.info("Sync engine disposed after schema creation.")


@pytest.fixture(scope="session")
def async_engine(postgres_container: str) -> AsyncEngine:
    """
    3) Provide a session-scoped *async* engine for the app code.
       We do *not* create or drop tables here. It's only used at runtime.
    """
    engine = create_async_engine(postgres_container, echo=False, future=True)
    yield engine
    # Container is ephemeral; no table drops needed
    logger.info("Disposing async engine at session end.")
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(engine.dispose())


@pytest.fixture(scope="function")
def client(async_engine: AsyncEngine) -> TestClient:
    """
    4) Override async_get_db so that each *request* uses a fresh async session
       in the exact event loop used by TestClient. This prevents
       "attached to a different loop" errors.
    """

    async def _override_async_get_db():
        async_session = async_sessionmaker(
            bind=async_engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            yield session

    # Override the normal async_get_db
    app.dependency_overrides[async_get_db] = _override_async_get_db

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
