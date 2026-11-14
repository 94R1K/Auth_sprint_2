from core.exceptions import ForbiddenError
from core.permissions import get_user_permission_codes
from db.dependencies import PostgresSession
from fastapi import Request
from schemas import UserRead

from .auth import CurrentUserDependency


async def _get_codes(
    request: Request,
    user: UserRead,
    session: PostgresSession,
) -> set[str]:
    """Ленивая загрузка прав в request.state (один SQL на запрос)."""

    if not hasattr(request.state, "permission_codes"):
        request.state.permission_codes = await get_user_permission_codes(
            session,
            user.id,
        )

    return request.state.permission_codes


def require_permission(code: str):
    async def checker(
        request: Request,
        user: CurrentUserDependency,
        session: PostgresSession,
    ) -> UserRead:
        if not user.is_active:
            raise ForbiddenError("Inactive user")

        if user.is_superuser:
            return user

        codes = await _get_codes(request, user, session)

        if code not in codes:
            raise ForbiddenError(f"Permission '{code}' required")

        return user

    return checker
