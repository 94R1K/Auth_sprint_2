from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from opentelemetry import trace


def register_middlewares(app: FastAPI) -> None:
    @app.middleware("http")
    async def before_request(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id")
        debug_id = request.headers.get("jaeger-debug-id")
        span = trace.get_current_span()

        if span.is_recording():
            if request_id:
                span.set_attribute("http.request_id", request_id)
            if debug_id:
                span.set_attribute("jaeger.debug_id", debug_id)

        if not request_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        response = await call_next(request)
        return response
