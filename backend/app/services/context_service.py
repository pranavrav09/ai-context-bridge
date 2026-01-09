from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List, Tuple
import logging

from app.models import Context, Message
from app.schemas import ContextCreate
from app.services.openai_service import generate_summary

logger = logging.getLogger(__name__)


async def create_context(db: AsyncSession, context_data: ContextCreate) -> Context:
    """
    Create new context with messages and optional AI summary.

    Args:
        db: Database session
        context_data: Context data from request

    Returns:
        Created Context object

    Raises:
        Exception: If context creation fails
    """
    # Generate AI summary if requested
    ai_summary_metadata = None
    summary = context_data.summary

    if context_data.generate_ai_summary:
        try:
            ai_result = await generate_summary(context_data.messages)
            summary = ai_result["summary"]
            ai_summary_metadata = {
                "tokens_used": ai_result["tokens_used"],
                "model": ai_result["model"],
                "generated_at": datetime.utcnow().isoformat(),
            }
            logger.info(f"Generated AI summary with {ai_result['tokens_used']} tokens")
        except Exception as e:
            # Fall back to client summary if AI fails
            logger.error(f"AI summary failed, using client summary: {e}")
            if not summary:
                # Create a basic summary if no client summary provided
                summary = f"Conversation with {len(context_data.messages)} messages"

    # Create context
    context = Context(
        platform=context_data.platform,
        message_count=len(context_data.messages),
        formatted_text=context_data.formatted,
        summary=summary,
        ai_summary_metadata=ai_summary_metadata,
        source_metadata=context_data.source_metadata,
    )

    db.add(context)
    await db.flush()  # Get context.id

    # Create messages
    for idx, msg in enumerate(context_data.messages):
        message = Message(
            context_id=context.id,
            role=msg.role,
            content=msg.content,
            message_timestamp=msg.timestamp,
            sequence_order=idx,
        )
        db.add(message)

    await db.commit()
    await db.refresh(context)

    logger.info(
        f"Created context {context.id} with {len(context_data.messages)} messages"
    )

    return context


async def get_context(db: AsyncSession, context_id: str) -> Optional[Context]:
    """
    Retrieve context with messages.

    Args:
        db: Database session
        context_id: UUID of context

    Returns:
        Context object or None if not found
    """
    result = await db.execute(
        select(Context)
        .options(selectinload(Context.messages))
        .where(Context.id == context_id)
    )
    context = result.scalar_one_or_none()

    if context:
        # Sort messages by sequence order
        context.messages.sort(key=lambda m: m.sequence_order)
        logger.info(f"Retrieved context {context_id}")

    return context


async def list_contexts(
    db: AsyncSession,
    platform: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Context], int]:
    """
    List contexts with pagination.

    Args:
        db: Database session
        platform: Optional platform filter
        limit: Number of results to return
        offset: Offset for pagination

    Returns:
        Tuple of (list of contexts, total count)
    """
    # Build query
    query = select(Context).order_by(Context.created_at.desc())

    if platform:
        query = query.where(Context.platform == platform)

    # Get total count
    count_query = select(func.count()).select_from(Context)
    if platform:
        count_query = count_query.where(Context.platform == platform)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    contexts = result.scalars().all()

    logger.info(f"Listed {len(contexts)} contexts (total: {total})")

    return list(contexts), total


async def delete_context(db: AsyncSession, context_id: str) -> bool:
    """
    Delete context and cascade delete messages.

    Args:
        db: Database session
        context_id: UUID of context to delete

    Returns:
        bool: True if deleted, False if not found
    """
    result = await db.execute(delete(Context).where(Context.id == context_id))
    await db.commit()

    deleted = result.rowcount > 0
    if deleted:
        logger.info(f"Deleted context {context_id}")
    else:
        logger.warning(f"Context {context_id} not found for deletion")

    return deleted


async def cleanup_expired_contexts(db: AsyncSession) -> int:
    """
    Delete expired contexts (run as cron job).

    Args:
        db: Database session

    Returns:
        int: Number of contexts deleted
    """
    result = await db.execute(
        delete(Context).where(Context.expires_at < datetime.utcnow())
    )
    await db.commit()

    count = result.rowcount
    if count > 0:
        logger.info(f"Cleaned up {count} expired contexts")

    return count
