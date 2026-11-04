import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models import User

logger = logging.getLogger(__name__)


class CreateService:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create_superuser(self):
        try:
            user = User(
                login=settings.superuser_login,
                password=settings.superuser_password,
                first_name="Admin",
                last_name="Admin"
            )
            user.is_superuser = True
            user.is_active = True

            self._session.add(user)
            await self._session.flush()
            await self._session.commit()
            logger.error("Суперпользователь создан")
        except IntegrityError as e:
            await self._session.rollback()
            if getattr(e.orig, "sqlstate", None) == "23505":
                logger.error("Superuser already exists")
            else:
                logger.error("Failed to create superuser")
                raise
