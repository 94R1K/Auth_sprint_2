from functools import partial

from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

password_hasher = PasswordHash.recommended()


async def hash_password(password: str) -> str:
    """Создать хеш пароля в отдельном потоке."""
    result: str = await run_in_threadpool(
        partial(password_hasher.hash, password),
    )
    return result


async def verify_password_and_update(
    password: str,
    password_hash: str,
) -> tuple[bool, str | None]:
    """Проверить пароль и обновить хеш при необходимости."""
    result: tuple[bool, str | None] = await run_in_threadpool(
        partial(
            password_hasher.verify_and_update,
            password,
            password_hash,
        ),
    )
    return result
