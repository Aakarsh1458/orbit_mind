from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

# Base class for SQLAlchemy ORM models
Base = declarative_base()

# Database engine initialization
database_url = settings.DATABASE_URL
engine_kwargs = {"echo": settings.DEBUG}

if "sqlite" in database_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

async_engine = create_async_engine(database_url, **engine_kwargs)
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session.
    Automatically handles commit and rollback on exceptions.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initializes tables in database."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.warning("Could not automatically initialize DB schema: %s", e)
