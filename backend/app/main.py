from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import engine, Base
from app.api.routes import contexts, summarize, health

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

    yield

    # Shutdown: cleanup if needed
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
