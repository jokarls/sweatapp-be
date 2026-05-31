import asyncio

import pytest
import pytest_asyncio
from asyncpg import create_pool
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
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

    # Run migrations/init script
    with open("sql/init.sql") as f:
        sql = f.read()
        async with pool.acquire() as conn:
            await conn.execute(sql)

    yield pool
    await pool.close()
