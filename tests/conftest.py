import logging
from typing import AsyncGenerator, Generator

import httpx
import pytest
import pytest_asyncio
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
        Generator[str, None, None]: Async connection string to postgres database.

    """
    logger.info("Starting Postgres test container...")
    with PostgresContainer("postgres:17") as container:
        container.start()

        raw_url = container.get_connection_url()
        async_url = raw_url.replace("psycopg2", "asyncpg")

        container_up_msg = f"Test container up => {async_url}"
        logger.info(container_up_msg)

        yield async_url

    logger.info("Postgres test container stopped.")


@pytest.fixture(scope="session", autouse=True)
def create_db_schema(postgres_container: str) -> None:
    """Create database schema synchronously (using psycopg2 driver).

    Args:
    ----
        postgres_container (str): Postgres container connection string.

    Returns:
    -------
        None

    """
    sync_url = postgres_container.replace("asyncpg", "psycopg2")

    create_schema_msg = f"Creating schema with sync engine => {sync_url}"
    logger.info(create_schema_msg)

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


@pytest_asyncio.fixture(scope="function")
async def async_engine(postgres_container: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create async database engine for the entire test session.

    Args:
    ----
        postgres_container (str): Postgres container connection string.

    Returns:
    -------
        AsyncGenerator[AsyncEngine, None]: Async database engine.

    """
    engine = create_async_engine(postgres_container, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(async_engine: AsyncEngine) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async client fixture that overrides the DB dependency with async sessions.

    Args:
    ----
        async_engine (AsyncEngine): Async database engine object.

    Returns:
    -------
        AsyncGenerator[AsyncClient, None]: Async client for interacting with FastAPI.

    """
    # Create the async session factory
    async_session = async_sessionmaker(
        bind=async_engine, expire_on_commit=False, class_=AsyncSession
    )

    # Override the FastAPI dependency to use this session factory
    async def _override_async_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session() as session:
            yield session

    app.dependency_overrides[async_get_db] = _override_async_get_db

    # Use httpx's ASGITransport to run requests against the FastAPI app in-memory
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # Clean up overrides after the test finishes
    app.dependency_overrides.clear()
