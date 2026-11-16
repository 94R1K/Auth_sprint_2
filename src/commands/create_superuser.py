import logging

from core.config import settings
from core.security.passwords import hash_password
from models import Role, User, UserRole
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class CreateService:
    ADMIN_ROLE_NAME = "admin"

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_superuser(self) -> None:
        try:
            # Получаем системную роль администратора.
            admin_role = await self._session.scalar(
                select(Role).where(
                    Role.name == self.ADMIN_ROLE_NAME,
                )
            )

            if admin_role is None:
                raise RuntimeError(
                    f"System role '{self.ADMIN_ROLE_NAME}' does not exist"
                )

            # Проверяем, существует ли пользователь.
            user = await self._session.scalar(
                select(User).where(
                    User.login == settings.superuser_login,
                )
            )

            if user is None:
                password_hash = await hash_password(
                    settings.superuser_password,
                )

                user = User(
                    login=settings.superuser_login,
                    password=password_hash,
                    first_name="Admin",
                    last_name="Admin",
                    is_superuser=True,
                    is_active=True,
                )

                self._session.add(user)
                await self._session.flush()
            else:
                user.is_superuser = True
                user.is_active = True

            # Проверяем, назначена ли пользователю роль администратора.
            user_role = await self._session.get(
                UserRole,
                (user.id, admin_role.id),
            )

            if user_role is None:
                self._session.add(
                    UserRole(
                        user_id=user.id,
                        role_id=admin_role.id,
                    )
                )

            await self._session.commit()

            logger.info("Superuser successfully created or updated")

        except IntegrityError:
            await self._session.rollback()
            logger.exception("Failed to create superuser")
            raise

        except Exception:
            await self._session.rollback()
            raise
