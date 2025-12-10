import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.utils.exceptions import AppException

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- Sentry Initialization ---
# Stage 21: Real-time monitoring
if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=settings.ENVIRONMENT,
    )
    logger.info("Sentry initialized.")


# --- Lifespan Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces the deprecated @app.on_event("startup").
    """
    logger.info("Ruvox Backend starting up...")
    
    # Place for future startup logic (e.g., DB connection checks, cache warm-up)
    
    yield
    
    logger.info("Ruvox Backend shutting down...")
    # Place for shutdown logic (e.g., closing thread pools)


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Ruvox Wallet API",
    description="Non-Custodial Stablecoin Wallet & Smart Contract Payment System API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)


# --- Middleware Configuration ---

# CORS (Cross-Origin Resource Sharing)
# Critical for mobile apps (Capacitor/Ionic) and Web Dashboards to communicate with the API.
if settings.ENVIRONMENT == "development":
    allow_origins = ["*"] # Allow all origins in development for easier testing
else:
    # In production, you might want to restrict this to your specific domains
    # or keep "*" if the API is public/mobile-first.
    allow_origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global Exception Handlers ---

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Global handler for all application-specific exceptions (from app.utils.exceptions).
    Ensures a consistent JSON error format across the entire API.
    """
    logger.error(f"AppException: {exc.detail} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected errors (e.g., 500 Internal Server Error).
    Prevents raw stack traces from leaking to the client in production.
    """
    logger.exception(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."},
    )


# --- Router Registration ---
app.include_router(api_router, prefix="/api/v1")


# --- Root Health Check ---
@app.get("/", tags=["Health"])
async def root():
    """
    Simple health check endpoint for load balancers and uptime monitoring.
    """
    return {
        "app_name": "Ruvox Wallet API",
        "status": "running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }