import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.time()
        logger.info(
            f"Incoming request {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )

        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        logger.info(
            f"Completed request {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.2f}ms",
            extra={"request_id": request_id}
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = f"{process_time:.2f}"
        return response
