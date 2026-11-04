from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import (
    AuthError,
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidAccessTokenError,
    LoginRateLimitExceeded,
    NotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(AuthError)
    async def auth_handler(request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(InvalidAccessTokenError)
    async def invalid_access_token_handler(
        request: Request,
        exc: InvalidAccessTokenError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(LoginRateLimitExceeded)
    async def login_rate_limit_handler(
        request: Request,
        exc: LoginRateLimitExceeded,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": exc.message},
            headers={"Retry-After": str(exc.retry_after)},
        )
