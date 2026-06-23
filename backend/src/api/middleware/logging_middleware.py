"""
Middleware — Request logging and global error handling.
"""
import logging
import time
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[{request_id}] {response.status_code} — {elapsed:.1f}ms")
        response.headers["X-Request-ID"] = request_id
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal server error: {str(e)}"},
            )
