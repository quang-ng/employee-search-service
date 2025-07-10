from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
# from sqlalchemy.exc import OperationalError, AuthenticationFailed
from app.db.models import Base
import os
import logging
import asyncio
from typing import Optional
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")


# Log DATABASE_URL if not in production
if ENVIRONMENT != "production":
    logger.info(f"Database URL: {DATABASE_URL}")

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
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {str(e)}")
        raise

async def get_db():
    """Get database session with retry logic and better error handling."""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to create database session (attempt {attempt + 1}/{max_retries})")
            async with AsyncSessionLocal() as session:
                # Test the connection with a simple query
                logger.info("Testing database connection...")
                await session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                try:
                    yield session
                    logger.info("Database session yielded successfully")
                except Exception as e:
                    logger.error(f"Error during session usage: {str(e)}")
                    await session.rollback()
                    raise
                finally:
                    logger.info("Database session cleanup completed")
                return  # Success, exit the function
        except HTTPException as e:
            logger.error(f"HTTPException, raise error!!, {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected database error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to create database session after {max_retries} attempts: {str(e)}")
                raise
            else:
                logger.info(f"Retrying database connection in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
