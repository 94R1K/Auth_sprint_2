from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import config as logging_config
from textwrap import dedent

from api.dependencies import require_global_user_rate_limit
from api.exception_handlers import register_exception_handlers
from api.middlewares import register_middlewares
from api.tracer import configure_tracer
from api.v1.register_routers import register_routers
from clients import OAuthStateCacheClient, RedisCacheClient
from core.config import settings
from core.logger import LOGGING
from core.security import RateLimiter
from db.postgres import engine
from fastapi import FastAPI
from fastapi.params import Depends
from redis.asyncio import Redis


logging_config.dictConfig(LOGGING)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    app.state.redis = redis

    cache_client = RedisCacheClient(redis)
    oauth_store_client = OAuthStateCacheClient(redis)

    app.state.redis_cache_client = cache_client
    app.state.oauth_store_client = oauth_store_client
    app.state.rate_limiter = RateLimiter(
        cache_client=cache_client,
    )

    try:
        await redis.ping()
        yield
    finally:
        try:
            await redis.aclose()
        finally:
            await engine.dispose()


tags_metadata = [
    {
        "name": "auth",
        "description": "Регистрация, аутентификация и управление пользовательскими сессиями",
    },
    {
        "name": "healthcheck",
        "description": "Проверка жизнеспособности сервиса",
    },
]


def create_fastapi_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        description=dedent(
            """
            API сервиса аутентификации и управления пользователями.

            Предоставляет возможности регистрации и аутентификации
            пользователей, выдачи и обновления токенов доступа,
            а также завершения пользовательской сессии.

            PostgreSQL используется для хранения учетных записей
            пользователей и refresh-токенов.

            Redis используется для хранения отозванных access-токенов
            и проверки их действительности.
            """
        ).strip(),
        openapi_tags=tags_metadata,
        version="1.0.0",
        docs_url="/api/openapi",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
        dependencies=[
            Depends(
                require_global_user_rate_limit(
                    user_limit=settings.user_rate_limit,
                    user_window=settings.user_rate_limit_window,
                )
            )
        ],
    )

    register_middlewares(app)
    register_exception_handlers(app)
    register_routers(app)
    configure_tracer(
        app,
        settings.jaeger_host,
        settings.jaeger_port,
        settings.jaeger_insecure,
        engine.sync_engine,
    )

    return app


fastapi_app = create_fastapi_app()
