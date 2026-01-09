from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
from app.database import Base
from app.config import settings


def generate_uuid():
    """Generate UUID as string for compatibility across databases"""
    return str(uuid.uuid4())


class Context(Base):
    __tablename__ = "contexts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform = Column(String(20), nullable=False, index=True)
    message_count = Column(Integer, nullable=False)
    formatted_text = Column(Text, nullable=False)
    summary = Column(Text)
    ai_summary_metadata = Column(JSON)  # JSONB in PostgreSQL, JSON in SQLite
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=settings.DEFAULT_RETENTION_DAYS),
        index=True,
    )
    source_metadata = Column(JSON)

    # Relationships
    messages = relationship("Message", back_populates="context", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Context(id={self.id}, platform={self.platform}, message_count={self.message_count})>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    context_id = Column(String(36), ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_timestamp = Column(DateTime, nullable=False)
    sequence_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    context = relationship("Context", back_populates="messages")

    __table_args__ = (
        Index("idx_context_sequence", "context_id", "sequence_order", unique=True),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, context_id={self.context_id}, seq={self.sequence_order})>"


class APIUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    request_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    response_status = Column(Integer)
    processing_time_ms = Column(Integer)

    __table_args__ = (
        Index("idx_ip_rate_limit", "ip_address", "request_timestamp"),
    )

    def __repr__(self):
        return f"<APIUsage(endpoint={self.endpoint}, status={self.response_status}, ip={self.ip_address})>"
