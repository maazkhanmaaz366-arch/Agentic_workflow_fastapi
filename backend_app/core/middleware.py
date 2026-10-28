import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class LoggingAndTimingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self,request:Request, call_next):
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())[:8]

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers['X-Process-Time'] = f"{duration_ms:.2f}"

        response.headers["X-Request-ID"] = request_id

        print(f"[{request.method}] {request.url.path} -> {response.status_code} {duration_ms:.2f} ms [id= {request_id}]")

        return response