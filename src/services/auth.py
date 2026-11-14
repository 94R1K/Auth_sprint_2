from typing import TYPE_CHECKING
from uuid import UUID

import jwt
from core.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    NotFoundError,
    UserInactiveError,
)
from core.repositories import UserRepositoryABC
from core.security import hash_password, verify_password_and_update
from core.services import AuthServiceABC, OAuthProviderABC, OAuthServiceABC
from pydantic import ValidationError


if TYPE_CHECKING:
    from core.dto import RefreshTokenClaims, TokenPair
    from models import User
    from schemas import UserCreate, UserInDB, UserLogin

    from services.token import TokenService


class AuthService(AuthServiceABC):
    def __init__(self, db: UserRepositoryABC, token_service: TokenService):
        self._db = db
        self._token_service = token_service

    async def create_user(self, user: UserCreate) -> UserInDB:
        hashed_password = await hash_password(user.password)
        user_with_hash = user.model_copy(update={"password": hashed_password})

        return await self._db.create_user(user=user_with_hash)

    async def login(
        self,
        *,
        user_data: UserLogin,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenPair:
        try:
            user: User = await self._db.get_user_by_login(login=user_data.login)
        except NotFoundError:
            raise InvalidCredentialsError("Неверный логин или пароль") from NotFoundError

        if not user.is_active:
            raise UserInactiveError("Пользователь деактивирован")

        if not user_data.password:
            raise InvalidCredentialsError("Неверный логин или пароль")

        is_valid, updated_password_hash = await verify_password_and_update(
            user_data.password,
            user.password,
        )
        if not is_valid:
            raise InvalidCredentialsError("Неверный логин или пароль")

        if updated_password_hash is not None:
            await self._db.update_password_hash(
                user_id=user.id,
                password_hash=updated_password_hash,
            )

        await self._db.create_login_history(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await self._token_service.get_tokens(user_id=user.id)

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        error_message = "Недействительный или просроченный токен обновления"
        try:
            claims: RefreshTokenClaims = self._token_service.decode_refresh_token(
                refresh_token
            )
        except (jwt.PyJWTError, ValidationError):
            raise InvalidRefreshTokenError(error_message) from None
        try:
            user_id: UUID = UUID(claims.user_id)
        except ValueError:
            raise InvalidRefreshTokenError(error_message) from ValueError

        user: User = await self._db.get_user_by_id(user_id=user_id)
        if not user.is_active:
            raise UserInactiveError("Пользователь деактивирован")

        return await self._token_service.refresh_tokens(
            claims=claims,
        )

    async def logout(self, user_id: str, session_id: str) -> None:
        await self._token_service.revoke_session(
            user_id=user_id,
            session_id=session_id,
        )

    async def logout_all_except_current(
        self, user_id: str, current_session_id: str
    ) -> None:
        await self._token_service.revoke_other_sessions(
            user_id=user_id,
            current_session_id=current_session_id,
        )

    async def logout_all(self, user_id: str) -> None:
        await self._token_service.revoke_all_user_tokens(user_id=user_id)


class OAuthService(OAuthServiceABC):
    def __init__(self, db, token_service, provider: OAuthProviderABC):
        self._db = db
        self._token_service = token_service
        self._provider = provider

    async def _get_or_create_user(self, user: UserCreate) -> User:
        try:
            return await self._db.get_user_by_login(login=user.login)
        except NotFoundError:
            return await self._db.create_user(
                user=user
            )

    def get_login_url(self) -> str:
        return self._provider.get_login_url()

    async def login(self, *, code: str, ip_address=None, user_agent=None) -> TokenPair:
        user_info = await self._provider.get_user_info(code)
        user = await self._get_or_create_user(user_info)

        await self._db.create_login_history(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await self._token_service.get_tokens(user_id=user.id)
