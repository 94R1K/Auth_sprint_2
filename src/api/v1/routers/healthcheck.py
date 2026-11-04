import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db.dependencies import PostgresSession, RedisClient

logger = logging.getLogger(__name__)

HEALTHCHECK_TIMEOUT = 2.0

healthcheck_router = APIRouter(
    prefix="/api/v1/health",
    tags=["healthcheck"],
)


class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]
    redis: Literal["ok", "unavailable"]


@healthcheck_router.get(
    "",
    summary="Проверить готовность API",
    description="Проверяет доступность PostgreSQL и Redis.",
    response_model=HealthCheckResponse,
    responses={
        503: {
            "model": HealthCheckResponse,
            "description": "Одна или несколько зависимостей недоступны",
        },
    },
)
async def health(
    response: Response,
    session: PostgresSession,
    redis: RedisClient,
) -> HealthCheckResponse:
    database_status: Literal["ok", "unavailable"] = "ok"
    redis_status: Literal["ok", "unavailable"] = "ok"

    try:
        await asyncio.wait_for(
            session.execute(text("SELECT 1")),
            timeout=HEALTHCHECK_TIMEOUT,
        )
    except (SQLAlchemyError, OSError, TimeoutError):
        logger.exception("Healthcheck: PostgreSQL is unavailable")
        database_status = "unavailable"

    try:
        await asyncio.wait_for(
            redis.ping(),
            timeout=HEALTHCHECK_TIMEOUT,
        )
    except (RedisError, OSError, TimeoutError):
        logger.exception("Healthcheck: Redis is unavailable")
        redis_status = "unavailable"

    is_healthy = database_status == "ok" and redis_status == "ok"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthCheckResponse(
        status="ok" if is_healthy else "error",
        database=database_status,
        redis=redis_status,
    )


@healthcheck_router.get(
    "/live",
    summary="Проверить работоспособность API",
    description="Проверяет, что приложение запущено и отвечает на запросы.",
)
async def liveness() -> dict[str, str]:
    return {"status": "ok"}
