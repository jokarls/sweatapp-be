from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asyncpg import create_pool
from fastapi import FastAPI

from app.api.routers import activities, webhooks
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Create DB pool
    app.state.pool = await create_pool(settings.DATABASE_URL)
    yield
    # Shutdown: Close DB pool
    await app.state.pool.close()


app = FastAPI(
    title="SweatCheck API",
    description="API for tracking sweat loss and fluid strategy",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(activities.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
