# services/dependencies.py
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Path

from clients import get_redis_cache_client
from core.clients import CacheClientABC
from core.config import settings
from core.exceptions import NotFoundError
from core.repositories import (
    PermissionRepositoryABC,
    RoleRepositoryABC,
    UserRepositoryABC,
)
from core.services import (
    AuthServiceABC,
    OAuthProviderABC,
    OAuthServiceABC,
    PermissionsServiceABC,
    RolesServiceABC,
    UserServiceABC,
)
from db.cache import CacheStorage
from db.dependencies import get_cache_storage
from repositories.dependencies import (
    get_permission_repository,
    get_role_repository,
    get_user_repository,
)

from .auth import AuthService, OAuthService
from .permissions import PermissionsService
from .providers import YandexOAuthProvider
from .roles import RolesServices
from .token import TokenService
from .users import UserService


@lru_cache
def get_oauth_registry() -> dict[str, OAuthProviderABC]:
    return {
        "yandex": YandexOAuthProvider(
            client_id = settings.yandex_client_id,
            secret = settings.yandex_secret_key,
            code_url = settings.yandex_code_url,
            token_url = settings.yandex_token_url,
            user_info_url = settings.yandex_user_info_url
        ),
    }


def get_oauth_service(
    code_provider: Annotated[str, Path()],
    repo: Annotated[UserRepositoryABC, Depends(get_user_repository)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    registry: Annotated[dict[str, OAuthProviderABC], Depends(get_oauth_registry)],
) -> OAuthServiceABC:
    try:
        provider = registry[code_provider]
    except KeyError:
        raise NotFoundError(f"Провайдер '{code_provider}' не подключен") from None
    return OAuthService(db=repo, token_service=token_service, provider=provider)


def get_token_service(
    cache_client: Annotated[CacheClientABC, Depends(get_redis_cache_client)],
):
    return TokenService(
        cache_client=cache_client,
        access_ttl=settings.access_token_ttl,
        refresh_ttl=settings.refresh_token_ttl,
        jwt_private_key=settings.jwt_private_key,
        jwt_public_key=settings.jwt_public_key,
    )


def get_auth_service(
    repo: Annotated[UserRepositoryABC, Depends(get_user_repository)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> AuthServiceABC:
    return AuthService(db=repo, token_service=token_service)


def get_user_service(
    repo: Annotated[UserRepositoryABC, Depends(get_user_repository)],
) -> UserServiceABC:
    return UserService(db=repo)


def get_role_service(
    repo: Annotated[RoleRepositoryABC, Depends(get_role_repository)],
    cache_storage: Annotated[CacheStorage, Depends(get_cache_storage)],
) -> RolesServiceABC:
    return RolesServices(db=repo, cache_storage=cache_storage)


def get_permission_service(
    repo: Annotated[PermissionRepositoryABC, Depends(get_permission_repository)],
    cache_storage: Annotated[CacheStorage, Depends(get_cache_storage)],
) -> PermissionsServiceABC:
    return PermissionsService(db=repo, cache_storage=cache_storage)
