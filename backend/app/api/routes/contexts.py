from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db
from app.schemas import (
    ContextCreate,
    ContextResponse,
    ContextListResponse,
    ContextListItem,
    ContextCreateResponse,
    MessageResponse,
)
from app.services import context_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/contexts", response_model=ContextCreateResponse, status_code=201)
async def create_context(
    context: ContextCreate, db: AsyncSession = Depends(get_db)
):
    """
    Save a new context with messages.

    - **platform**: Source AI platform (chatgpt, claude, gemini, poe)
    - **messages**: Array of conversation messages
    - **formatted**: Markdown formatted conversation
    - **summary**: Optional client-generated summary
    - **generate_ai_summary**: Whether to generate AI summary using GPT-4
    - **source_metadata**: Optional metadata about source
    """
    try:
        created_context = await context_service.create_context(db, context)
        return ContextCreateResponse(
            success=True,
            context_id=created_context.id,
            message_count=created_context.message_count,
            ai_summary=created_context.summary,
            created_at=created_context.created_at,
            url=f"/api/v1/contexts/{created_context.id}",
        )
    except Exception as e:
        logger.error(f"Failed to create context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contexts/{context_id}", response_model=ContextResponse)
async def get_context(context_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a specific context with all messages.

    - **context_id**: UUID of the context
    """
    context = await context_service.get_context(db, context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    # Convert messages to response format
    message_responses = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            timestamp=msg.message_timestamp,
            sequence_order=msg.sequence_order,
        )
        for msg in context.messages
    ]

    return ContextResponse(
        id=context.id,
        platform=context.platform,
        message_count=context.message_count,
        messages=message_responses,
        formatted=context.formatted_text,
        summary=context.summary,
        created_at=context.created_at,
        updated_at=context.updated_at,
    )


@router.get("/contexts", response_model=ContextListResponse)
async def list_contexts(
    platform: Optional[str] = Query(
        None, pattern="^(chatgpt|claude|gemini|poe)$", description="Filter by platform"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    List contexts with pagination and optional filtering.

    - **platform**: Optional filter by AI platform
    - **limit**: Maximum results to return (1-100)
    - **offset**: Offset for pagination
    """
    contexts, total = await context_service.list_contexts(
        db, platform=platform, limit=limit, offset=offset
    )

    context_items = [
        ContextListItem(
            id=c.id,
            platform=c.platform,
            message_count=c.message_count,
            summary=c.summary,
            created_at=c.created_at,
        )
        for c in contexts
    ]

    return ContextListResponse(
        contexts=context_items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.delete("/contexts/{context_id}", status_code=204)
async def delete_context(context_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a context and all associated messages.

    - **context_id**: UUID of the context to delete
    """
    deleted = await context_service.delete_context(db, context_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Context not found")
    return None
