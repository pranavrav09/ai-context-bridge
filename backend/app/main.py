from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.config import settings
from app.database import engine, Base
from app.api.routes import contexts, summarize, health
from app.middleware.rate_limit import limiter
from app.middleware.api_usage import APIUsageMiddleware
from app.services.context_service import cleanup_expired_contexts
from app.database import AsyncSessionLocal
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Create tables if not exist
    logger.info("Starting up AI Context Bridge API...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(_cleanup_loop())

    yield

    # Shutdown: cleanup if needed
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    logger.info("Shutting down AI Context Bridge API...")
    await engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title="AI Context Bridge API",
    version="1.0.0",
    description="Cloud storage and AI summarization for AI Context Bridge Chrome extension",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# API usage logging
app.add_middleware(APIUsageMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(contexts.router, prefix="/api/v1", tags=["Contexts"])
app.include_router(summarize.router, prefix="/api/v1", tags=["Summarization"])


async def _cleanup_loop():
    """
    Periodically delete expired contexts.
    """
    while True:
        try:
            async with AsyncSessionLocal() as session:
                await cleanup_expired_contexts(session)
        except Exception as e:
            logger.error(f"Expiration cleanup failed: {e}")
        await asyncio.sleep(settings.CLEANUP_INTERVAL_SECONDS)


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "name": "AI Context Bridge API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENV == "development",
        log_level=settings.LOG_LEVEL,
    )
