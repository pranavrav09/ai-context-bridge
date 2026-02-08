import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import AsyncSessionLocal
from app.models import APIUsage


class APIUsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            processing_ms = int((time.time() - start) * 1000)
            status_code = response.status_code if response else 500
            client_host = request.client.host if request.client else None

            async with AsyncSessionLocal() as session:
                session.add(
                    APIUsage(
                        endpoint=request.url.path,
                        ip_address=client_host,
                        user_agent=request.headers.get("user-agent"),
                        response_status=status_code,
                        processing_time_ms=processing_ms,
                    )
                )
                await session.commit()
