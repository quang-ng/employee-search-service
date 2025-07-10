from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.api import employees
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Ensure auth dependency is available
import app.middleware.auth

app = FastAPI()


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


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}", exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(employees.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
