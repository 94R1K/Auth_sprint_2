import base64
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import aiohttp
import jwt
from core.config import settings
from core.dto import AccessTokenClaims, RefreshTokenClaims, TokenPair
from core.exceptions import InvalidRefreshTokenError
from schemas import UserCreate


if TYPE_CHECKING:
    from core.clients import CacheClientABC


class TokenService:
    USER_SESSIONS_PREFIX = "auth:user:{user_id}:session:"
    SESSION_KEY = "auth:user:{user_id}:session:{session_id}"

    def __init__(
        self,
        *,
        cache_client: CacheClientABC,
        access_ttl: int,
        refresh_ttl: int,
        jwt_private_key: str,
        jwt_public_key: str,
    ) -> None:
        if access_ttl <= 0 or refresh_ttl <= 0:
            raise ValueError("Token TTL must be positive")

        self._cache_client = cache_client
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl
        self._jwt_private_key = jwt_private_key
        self._jwt_public_key = jwt_public_key

    def _session_key(self, user_id: str, session_id: str) -> str:
        """Сформировать ключ Redis для конкретной сессии пользователя."""
        return self.SESSION_KEY.format(
            user_id=user_id,
            session_id=session_id,
        )

    def _user_sessions_prefix(self, user_id: str) -> str:
        """Сформировать префикс Redis-ключей всех сессий пользователя."""
        return self.USER_SESSIONS_PREFIX.format(user_id=user_id)

    def _encode_token(
        self,
        claims: AccessTokenClaims | RefreshTokenClaims,
    ) -> str:
        """Подписать claims приватным ключом и получить JWT."""
        return jwt.encode(
            claims.model_dump(mode="json"),
            self._jwt_private_key,
            algorithm=settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        """Проверить подпись и срок действия access-токена."""
        payload = jwt.decode(
            token,
            self._jwt_public_key,
            algorithms=[settings.jwt_algorithm],
        )
        return AccessTokenClaims.model_validate(payload)

    def decode_refresh_token(self, token: str) -> RefreshTokenClaims:
        """Проверить подпись и срок действия refresh-токена."""
        payload = jwt.decode(
            token,
            self._jwt_public_key,
            algorithms=[settings.jwt_algorithm],
        )
        return RefreshTokenClaims.model_validate(payload)

    async def _create_token_pair(
        self,
        user_id: str,
        session_id: str,
        *,
        expected_refresh_jti: str | None = None,
    ) -> TokenPair:
        now = int(time.time())

        access_claims = AccessTokenClaims(
            user_id=user_id,
            session_id=session_id,
            jti=str(uuid4()),
            type="access",
            exp=now + self._access_ttl,
        )
        refresh_claims = RefreshTokenClaims(
            user_id=user_id,
            session_id=session_id,
            jti=str(uuid4()),
            type="refresh",
            exp=now + self._refresh_ttl,
        )

        access_token = self._encode_token(access_claims)
        refresh_token = self._encode_token(refresh_claims)

        if expected_refresh_jti is None:
            await self.add_refresh_token(refresh_claims)
        else:
            replaced = await self._cache_client.compare_and_set(
                key=self._session_key(user_id, session_id),
                expected=expected_refresh_jti,
                value=refresh_claims.jti,
                exat=refresh_claims.exp,
            )
            if not replaced:
                raise InvalidRefreshTokenError(
                    "Недействительный или просроченный токен обновления"
                )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def get_tokens(self, user_id: UUID) -> TokenPair:
        """Выпустить пару токенов для новой сессии."""
        return await self._create_token_pair(
            user_id=str(user_id),
            session_id=str(uuid4()),
        )

    async def add_refresh_token(
        self,
        claims: RefreshTokenClaims,
    ) -> None:
        """Создать или обновить состояние сессии."""
        key = self._session_key(
            user_id=claims.user_id,
            session_id=claims.session_id,
        )

        await self._cache_client.set(
            key=key,
            value=claims.jti,
            exat=claims.exp,
        )

    async def is_session_active(
        self,
        user_id: str,
        session_id: str,
    ) -> bool:
        """Проверить наличие активной сессии."""
        result = await self._cache_client.get(
            key=self._session_key(user_id, session_id),
        )
        return result is not None

    async def is_access_token_active(
        self,
        claims: AccessTokenClaims,
    ) -> bool:
        """Access-токен активен, пока активна его сессия."""
        return await self.is_session_active(
            user_id=claims.user_id,
            session_id=claims.session_id,
        )

    async def is_refresh_token_active(
        self,
        claims: RefreshTokenClaims,
    ) -> bool:
        """Проверить, существует ли refresh-токен текущей в сессии."""
        result = await self._cache_client.get(
            key=self._session_key(
                user_id=claims.user_id,
                session_id=claims.session_id,
            ),
        )
        return result == claims.jti

    async def refresh_tokens(self, claims: RefreshTokenClaims) -> TokenPair:
        """Обновить пару токенов с ротацией refresh-токена."""
        error_message = "Недействительный или просроченный токен обновления"

        if claims.type != "refresh":
            raise InvalidRefreshTokenError(error_message)

        try:
            user_id = UUID(claims.user_id)
        except ValueError:
            raise InvalidRefreshTokenError(error_message) from None

        return await self._create_token_pair(
            user_id=str(user_id),
            session_id=claims.session_id,
            expected_refresh_jti=claims.jti,
        )

    async def revoke_session(
        self,
        user_id: str,
        session_id: str,
    ) -> None:
        """Завершить сессию и отозвать связанные с ней токены."""
        await self._cache_client.delete(
            key=self._session_key(user_id, session_id),
        )

    async def revoke_other_sessions(
        self,
        user_id: str,
        current_session_id: str,
    ) -> None:
        """Завершить все сессии пользователя, кроме текущей."""
        prefix = self._user_sessions_prefix(user_id)
        keys = await self._cache_client.get_keys_by_prefix(
            prefix=prefix,
        )

        current_key = self._session_key(
            user_id=user_id,
            session_id=current_session_id,
        )

        for key in keys:
            if key != current_key:
                await self._cache_client.delete(key)

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Завершить все сессии пользователя."""
        await self._cache_client.delete_by_prefix(
            prefix=self._user_sessions_prefix(user_id),
        )


class YandexTokenService:
    def _get_authorization_headers(self) -> str:
        credentials = f"{settings.yandex_client_id}:{settings.yandex_secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def get_tokens(self, code: str) -> dict[str, Any]:
        if not settings.token_debug_mode:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-type": "application/x-www-form-urlencoded",
                    "Authorization": self._get_authorization_headers()
                }
                params = {
                    "grant_type": "authorization_code",
                    "code": code,
                }
                async with session.post(settings.yandex_token_url, params=params, headers=headers) as response:
                    return await response.json()
        return {
            "access_token": settings.yandex_debug_token,
            "refresh_token": settings.yandex_debug_token
        }

    async def get_user_info(self, access_token: str) -> UserCreate:
        async with aiohttp.ClientSession() as session:
            params = {
                "format": "json"
            }
            headers = {
                "Authorization": access_token
            }
            async with session.get(settings.yandex_user_info_url, params=params, headers=headers) as response:
                user_info = await response.json()
                return UserCreate(
                    login=user_info["login"],
                    first_name=user_info["first_name"],
                    last_name=user_info["last_name"],
                    auth_provider="yandex",
                )
