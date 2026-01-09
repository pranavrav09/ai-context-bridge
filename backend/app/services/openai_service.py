from openai import AsyncOpenAI
from app.config import settings
from app.schemas import MessageCreate
from typing import List
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
if settings.OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
else:
    logger.warning("OpenAI API key not configured. AI summarization will not be available.")


async def generate_summary(messages: List[MessageCreate], max_tokens: int = 150) -> dict:
    """
    Generate AI summary using GPT-4.

    Args:
        messages: List of messages to summarize
        max_tokens: Maximum tokens for summary

    Returns:
        dict with 'summary', 'tokens_used', 'model'

    Raises:
        Exception: If OpenAI API call fails
    """
    if not client:
        raise Exception("OpenAI API key not configured")

    # Construct conversation text
    conversation_text = "\n\n".join(
        [f"{msg.role.upper()}: {msg.content}" for msg in messages]
    )

    # Create prompt
    prompt = f"""Summarize the following conversation concisely. Focus on:
1. Main topics discussed
2. Key questions asked
3. Important conclusions or decisions
4. Overall context and purpose

Conversation:
{conversation_text}

Provide a summary in 2-3 sentences that captures the essence of this conversation."""

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries of AI conversations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for more focused summaries
        )

        summary = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        model = response.model

        logger.info(f"Generated summary using {model}, tokens: {tokens_used}")

        return {
            "summary": summary,
            "tokens_used": tokens_used,
            "model": model,
        }

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise Exception(f"Failed to generate AI summary: {str(e)}")


async def is_openai_available() -> bool:
    """
    Check if OpenAI API is available and configured.

    Returns:
        bool: True if OpenAI is available
    """
    return client is not None and settings.OPENAI_API_KEY != ""
