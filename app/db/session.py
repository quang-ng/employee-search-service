from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
# from sqlalchemy.exc import OperationalError, AuthenticationFailed
from app.db.models import Base
import os
import asyncio
from typing import Optional
from fastapi import HTTPException
from app.config.logging import setup_logging
import structlog

# Configure structlog JSON logging (idempotent)
setup_logging()
logger = structlog.get_logger()

DATABASE_URL = os.getenv("DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")


# Create engine with better configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Maximum overflow connections
    pool_reset_on_return='commit',
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "server_settings": {
            "application_name": "employee_search_service"
        }
    }
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("db_tables_initialized")
    except Exception as e:
        logger.error("db_init_failed", error=str(e))
        raise

async def get_db():
    """Get database session with retry logic and better error handling."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info("db_session_attempt", attempt=attempt + 1, max_retries=max_retries)
            async with AsyncSessionLocal() as session:
                try:
                    yield session
                except Exception as e:
                    logger.error("db_session_usage_error", error=str(e))
                    await session.rollback()
                    raise
                finally:
                    return  # Success, exit the function
        except HTTPException as e:
            logger.error("db_http_exception", error=str(e))
            raise e
        except Exception as e:
            logger.error("db_unexpected_error", attempt=attempt + 1, max_retries=max_retries, error=str(e))
            if attempt == max_retries - 1:
                logger.error("db_session_failed", error=str(e))
                raise
            else:
                logger.info("db_retrying", retry_delay=retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
