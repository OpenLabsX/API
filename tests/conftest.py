import logging
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from src.app.core.db.database import Base, async_get_db
from src.app.main import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[str, None, None]:
    """Get connection string to Postgres container.

    Returns
    -------
        str: Conenction string to Postgres container.

    """
    logger.info("Starting Postgres test container...")
    with PostgresContainer("postgres:17") as container:
        container.start()

        raw_url = container.get_connection_url()

        # Convert to async driver for the app
        async_url = raw_url.replace("psycopg2", "asyncpg")

        msg = f"Test container up => {async_url}"
        logger.info(msg)

        yield async_url

    logger.info("Postgres test container stopped.")


@pytest.fixture(scope="session", autouse=True)
def create_db_schema(postgres_container: str) -> None:
    """Create database schema synchronously.

    Returns
    -------
        None

    """
    # Replace 'asyncpg' -> 'psycopg2' for the sync engine
    sync_url = postgres_container.replace("asyncpg", "psycopg2")
    schema_msg = f"Creating schema with sync engine => {sync_url}"
    logger.info(schema_msg)

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
def async_engine(postgres_container: str) -> Generator[AsyncEngine, None, None]:
    """Create async database engine.

    Returns
    -------
        AsyncEngine: Async database engine.

    """
    engine = create_async_engine(postgres_container, echo=False, future=True)
    yield engine

    # Container is ephemeral; no table drops needed
    logger.info("Disposing async engine at session end.")
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(engine.dispose())


@pytest.fixture(scope="function")
def client(async_engine: AsyncEngine) -> Generator[TestClient, None, None]:
    """Create test client with connection to test database.

    Returns
    -------
        TestClient: Database connected TestClient.

    """

    async def _override_async_get_db() -> AsyncGenerator[AsyncSession, None]:
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
