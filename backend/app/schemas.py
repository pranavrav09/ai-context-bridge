from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=100000)
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2025-01-08T10:30:00Z"
            }
        }


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime
    sequence_order: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2025-01-08T10:30:00Z",
                "sequence_order": 0
            }
        }
    }


class ContextCreate(BaseModel):
    platform: str = Field(..., pattern="^(chatgpt|claude|gemini|poe)$")
    messages: List[MessageCreate] = Field(..., min_length=1, max_length=500)
    formatted: str = Field(..., min_length=1)
    summary: Optional[str] = None
    generate_ai_summary: bool = False
    source_metadata: Optional[dict] = None

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v):
        if len(v) > 500:
            raise ValueError("Maximum 500 messages per context")
        if len(v) == 0:
            raise ValueError("At least one message is required")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "platform": "chatgpt",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, how are you?",
                        "timestamp": "2025-01-08T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "I'm doing well, thank you!",
                        "timestamp": "2025-01-08T10:30:05Z"
                    }
                ],
                "formatted": "## Full Conversation\n\n**USER**: Hello...",
                "summary": "Greeting exchange",
                "generate_ai_summary": True,
                "source_metadata": {
                    "browser": "Chrome",
                    "extension_version": "1.0.0"
                }
            }
        }
    }


class ContextResponse(BaseModel):
    id: str
    platform: str
    message_count: int
    messages: List[MessageResponse]
    formatted: str
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContextListItem(BaseModel):
    id: str
    platform: str
    message_count: int
    summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ContextListResponse(BaseModel):
    contexts: List[ContextListItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class ContextCreateResponse(BaseModel):
    success: bool
    context_id: str
    message_count: int
    ai_summary: Optional[str]
    created_at: datetime
    url: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "context_id": "550e8400-e29b-41d4-a716-446655440000",
                "message_count": 2,
                "ai_summary": "Greeting exchange with polite introduction",
                "created_at": "2025-01-08T10:31:00Z",
                "url": "/api/v1/contexts/550e8400-e29b-41d4-a716-446655440000"
            }
        }
    }


class SummarizeRequest(BaseModel):
    messages: List[MessageCreate]
    max_tokens: int = Field(default=150, ge=50, le=500)

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain quantum computing",
                        "timestamp": "2025-01-08T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Quantum computing uses quantum bits...",
                        "timestamp": "2025-01-08T10:30:05Z"
                    }
                ],
                "max_tokens": 150
            }
        }
    }


class SummarizeResponse(BaseModel):
    summary: str
    tokens_used: int
    model: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "summary": "User asked about quantum computing; assistant provided basic explanation...",
                "tokens_used": 234,
                "model": "gpt-4-turbo-preview"
            }
        }
    }


class HealthResponse(BaseModel):
    status: str
    database: str
    openai: str
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "database": "connected",
                "openai": "configured",
                "timestamp": "2025-01-08T10:31:00Z"
            }
        }
    }


class ErrorResponse(BaseModel):
    detail: str
    status_code: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Context not found",
                "status_code": 404
            }
        }
    }
