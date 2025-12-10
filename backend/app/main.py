import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.websocket_service import websocket_manager
from app.utils.exceptions import AppException

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- Sentry Setup (Production Observability) ---
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
    )

# --- Lifespan Events (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    Crucial for initializing Redis Pub/Sub listeners and DB pools.
    """
    logger.info("Application starting up...")
    
    # 1. Start WebSocket Redis Listener
    await websocket_manager.start()
    
    yield
    
    logger.info("Application shutting down...")
    
    # 2. Stop WebSocket Redis Listener
    await websocket_manager.stop()
    
    # 3. Close DB Connections (Handled by Engine disposal usually, but good practice if manual)
    from app.db.session import async_engine
    await async_engine.dispose()

# --- App Definition ---
app = FastAPI(
    title="Ruvox Wallet API",
    version="1.0.0",
    description="Production-ready Solana/EVM/Bitcoin Wallet Backend",
    openapi_url="/api/v1/openapi.json" if settings.ENVIRONMENT == "development" else None, # Hide docs in prod
    lifespan=lifespan,
)

# --- Middleware ---

# 1. Trusted Host (Prevent Host Header Injection)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"] # Restrict this in production to your domain (e.g. ["api.ruvox.com"])
)

# 2. CORS (Cross-Origin Resource Sharing)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Exception Handlers ---

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle our custom defined exceptions (e.g., InsufficientBalance, NotFound).
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unhandled exceptions to prevent stack trace leakage.
    """
    logger.error(f"Unhandled Internal Server Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support."}
    )

# --- Router Registration ---
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Load Balancers (AWS ALB).
    """
    return {"status": "ok", "version": "1.0.0"}