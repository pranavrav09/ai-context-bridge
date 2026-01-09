from fastapi import APIRouter, HTTPException
import logging

from app.schemas import SummarizeRequest, SummarizeResponse
from app.services.openai_service import generate_summary, is_openai_available

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_messages(request: SummarizeRequest):
    """
    Generate AI summary for provided messages (standalone operation).

    - **messages**: Array of messages to summarize
    - **max_tokens**: Maximum tokens for summary (50-500)

    This endpoint can be used independently to get AI summaries
    without saving the context to the database.
    """
    if not await is_openai_available():
        raise HTTPException(
            status_code=503,
            detail="OpenAI API is not configured. Please set OPENAI_API_KEY environment variable.",
        )

    try:
        result = await generate_summary(request.messages, request.max_tokens)
        return SummarizeResponse(
            summary=result["summary"],
            tokens_used=result["tokens_used"],
            model=result["model"],
        )
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        if "quota" in str(e).lower() or "payment" in str(e).lower():
            raise HTTPException(
                status_code=402, detail="OpenAI API quota exceeded or payment required"
            )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {str(e)}"
        )
