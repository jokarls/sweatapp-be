import asyncio
import os

# Set default mock environment variables for test suite execution
os.environ.setdefault("STRAVA_CLIENT_ID", "mock_strava_client_id")
os.environ.setdefault("STRAVA_CLIENT_SECRET", "mock_strava_client_secret")
os.environ.setdefault("OPENWEATHERMAP_API_KEY", "mock_openweathermap_api_key")

import pytest
import pytest_asyncio
from asyncpg import create_pool
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def db_pool(postgres_container):
    # testcontainers returns 'postgresql+psycopg2://...'
    # asyncpg only wants 'postgresql://...'
    connection_url = postgres_container.get_connection_url().replace("+psycopg2", "")

    pool = await create_pool(connection_url)

    # Run database migrations
    from app.infrastructure.db.migrations import run_migrations
    await run_migrations(pool)

    yield pool
    await pool.close()
