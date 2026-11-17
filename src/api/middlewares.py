from typing import TYPE_CHECKING

from api.dependencies import get_client_ip
from core.config import settings
from core.dto import RateLimitRule
from core.security import RateLimitKey, hash_rate_limit_value
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from opentelemetry import trace
from starlette.middleware.base import RequestResponseEndpoint


if TYPE_CHECKING:
    from core.security import RateLimiter


def register_middlewares(app: FastAPI) -> None:
    # @app.middleware("http")
    # async def before_request(
    #     request: Request, call_next: RequestResponseEndpoint
    # ) -> Response:
    #     request_id = request.headers.get("X-Request-Id")
    #     debug_id = request.headers.get("jaeger-debug-id")
    #     span = trace.get_current_span()

    #     if span.is_recording():
    #         if request_id:
    #             span.set_attribute("http.request_id", request_id)
    #         if debug_id:
    #             span.set_attribute("jaeger.debug_id", debug_id)

    #     if not request_id:
    #         return JSONResponse(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             content={"detail": "X-Request-Id is required"},
    #         )
    #     return await call_next(request)

    @app.middleware("http")
    async def global_ip_rate_limit(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rate_limiter: RateLimiter = request.app.state.rate_limiter

        client_ip = get_client_ip(request)
        ip_hash = hash_rate_limit_value(client_ip)

        retry_after = await rate_limiter.check(
            rules=(
                RateLimitRule(
                    key=RateLimitKey.ip(
                        ip_hash=ip_hash,
                    ),
                    limit=settings.ip_rate_limit,
                    window=settings.ip_rate_limit_window,
                ),
            ),
        )

        if retry_after is not None:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Слишком много запросов. Повторите позже."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
