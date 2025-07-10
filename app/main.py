from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from app.api import employees
from app.db.session import engine, init_db
import asyncio
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Ensure auth dependency is available
import app.middleware.auth

app = FastAPI()

# Set up the limiter (per IP by default, can be customized)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# Override the default HTTPException handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.info(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={"detail": exc.detail or "Authentication required"},
            headers={"WWW-Authenticate": "Basic"},
        )
    elif exc.status_code == 429:
        return JSONResponse(
            status_code=429,
            content={
                "detail": exc.detail or "Rate limit exceeded. Please try again later."
            },
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail or "An error occurred"},
        )


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}", exc_info=True
    )

    # Check if this is actually an HTTPException that wasn't caught
    if isinstance(exc, HTTPException):
        logger.warning(
            f"HTTPException caught by general handler: {exc.status_code} - {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail or "An error occurred"},
            headers=getattr(exc, "headers", {}),
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    logger.info("Shutting down Employee Search Service...")
    await engine.dispose()
    logger.info("Database connections closed")


app.include_router(employees.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
