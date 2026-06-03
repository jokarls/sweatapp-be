import logging
from pathlib import Path

from asyncpg import Pool

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sql" / "migrations"


async def run_migrations(pool: Pool) -> None:
    """
    Automatically runs any pending database migrations in the sql/migrations folder
    using a transaction-level advisory lock to ensure concurrency safety.
    """
    if not MIGRATIONS_DIR.exists():
        logger.warning(f"Migrations directory not found at {MIGRATIONS_DIR}")
        return

    # Get sorted list of migration SQL files
    migration_files = sorted(
        [f for f in MIGRATIONS_DIR.glob("*.sql") if f.is_file()],
        key=lambda p: p.name
    )

    if not migration_files:
        logger.info("No migration files found.")
        return

    logger.info(f"Checking for database migrations in {MIGRATIONS_DIR}...")

    # Acquire a connection and run migrations in a single transaction
    async with pool.acquire() as conn, conn.transaction():
        # 1. Acquire transaction-level advisory lock to prevent concurrent runs
        # (e.g. multi-container Cloud Run startup).
        # 123456 is an arbitrary 64-bit integer representing our lock key.
        await conn.execute("SELECT pg_advisory_xact_lock(123456);")

        # 2. Create the schema_version table if it doesn't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version VARCHAR(50) PRIMARY KEY,
                description VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Retrieve already applied migrations
        rows = await conn.fetch("SELECT version FROM schema_version;")
        applied_versions = {row["version"] for row in rows}

        # 4. Apply pending migrations
        for path in migration_files:
            filename = path.name
            # Filename format expected: e.g. 0001_init.sql or 0002__add_index.sql
            version = filename.split(".")[0]
            
            if version in applied_versions:
                continue

            logger.info(f"Applying database migration: {filename}...")
            
            with open(path, encoding="utf-8") as f:
                sql_content = f.read()

            # Run the migration
            await conn.execute(sql_content)

            # Record migration in history
            description = version.split("__")[-1] if "__" in version else version
            await conn.execute(
                "INSERT INTO schema_version (version, description) VALUES ($1, $2);",
                version,
                description
            )
            logger.info(f"Successfully applied database migration: {filename}")

    logger.info("Database migration check completed successfully.")
