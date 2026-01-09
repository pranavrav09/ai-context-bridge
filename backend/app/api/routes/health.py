from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import logging

from app.database import get_db
from app.schemas import HealthResponse
from app.services.openai_service import is_openai_available

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for monitoring.

    Returns:
    - **status**: Overall health status
    - **database**: Database connection status
    - **openai**: OpenAI API configuration status
    - **timestamp**: Current server timestamp
    """
    # Check database connection
    database_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = f"error: {str(e)}"

    # Check OpenAI configuration
    openai_status = "not_configured"
    if await is_openai_available():
        openai_status = "configured"

    # Overall status
    overall_status = "healthy" if database_status == "connected" else "unhealthy"

    return HealthResponse(
        status=overall_status,
        database=database_status,
        openai=openai_status,
        timestamp=datetime.utcnow(),
    )
