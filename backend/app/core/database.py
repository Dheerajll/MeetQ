# SQLAlchemy async database configuration
# Sets up async engine, SessionLocal for dependency injection, and declarative Base
"""
Async SQLAlchemy engine and session management.
"""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# 1. The Async Engine
# This manages the connection pool to your local PostgreSQL.
# `echo=True` will print raw SQL queries to the console if DEBUG is true.
# `pool_pre_ping=True` ensures dead connections are recycled automatically.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


# 2. The Session Factory
# We use this to create new database sessions for each request.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. The Base Class
# Every ORM model (User, Meeting, etc.) will inherit from this.
class Base(DeclarativeBase):
    pass

# 4. FastAPI Dependency Injection
# This is an async generator. FastAPI will use it like:
# @router.get("/items")
# async def get_items(db: AsyncSession = Depends(get_db)):
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # If the endpoint finishes without errors, commit the transaction
            await session.commit()
        except Exception:
            # If an error occurs, rollback any pending changes
            await session.rollback()
            raise