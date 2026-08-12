"""Database engine and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def migrate_db() -> None:
    """Add new columns to existing tables safely (idempotent)."""
    from sqlalchemy import text

    new_columns = [
        ("findings", "cvss_score", "FLOAT"),
        ("findings", "cvss_vector", "VARCHAR(256)"),
        ("scan_jobs", "tags", "VARCHAR(512)"),
        ("findings", "mitre_techniques", "VARCHAR(256)"),
        ("findings", "owasp_category", "VARCHAR(128)"),
        ("findings", "is_new", "BOOLEAN DEFAULT true"),
        ("reports", "threat_narrative", "TEXT"),
    ]
    async with engine.begin() as conn:
        for table, col, coltype in new_columns:
            try:
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception:
                pass


async def init_db() -> None:
    """Create all tables (dev convenience — use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await migrate_db()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with async_session() as session:
        yield session
