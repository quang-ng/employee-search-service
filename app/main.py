from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.api import employees
from app.config.logging import setup_logging
import structlog
from prometheus_client import make_asgi_app, Counter, Histogram
import time

# Configure structlog JSON logging
setup_logging()
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

# Ensure auth dependency is available
import app.middleware.auth

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(process_time)
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.info("http_exception", status_code=exc.status_code, detail=exc.detail)

    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={"detail": exc.detail or "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
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
        "unhandled_exception", exc_type=type(exc).__name__, exc=str(exc), exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(employees.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
