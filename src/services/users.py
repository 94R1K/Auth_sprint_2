from uuid import UUID

from core.dto import LimitOffsetParams
from core.exceptions import InvalidCredentialsError, NotFoundError, UserInactiveError
from core.repositories import UserRepositoryABC
from core.services.users import UserServiceABC
from schemas import LoginHistoryRead, UserRead, UserUpdate


class UserService(UserServiceABC):
    def __init__(self, db: UserRepositoryABC):
        self._db = db

    async def get_user_by_id(self, user_id: UUID) -> UserRead:
        user = await self._db.get_user_by_id(user_id=user_id)

        if not user.is_active:
            raise UserInactiveError("Пользователь деактивирован")

        return UserRead.model_validate(user)

    async def get_user_by_login(self, login: str) -> UserRead:
        try:
            user = await self._db.get_user_by_login(login=login)
        except NotFoundError:
            raise InvalidCredentialsError(
                "Неверный логин или пароль"
            ) from None

        if not user.is_active:
            raise UserInactiveError("Пользователь деактивирован")

        return UserRead.model_validate(user)

    async def update_me(self, user_id: UUID, user: UserUpdate) -> UserRead:
        updated_user = await self._db.update_me(user_id=user_id, new_user_data=user)
        if not updated_user:
            raise NotFoundError("")

        return updated_user

    async def get_login_history_by_user_id(
        self, user_id: UUID, params: LimitOffsetParams
    ) -> list[LoginHistoryRead]:
        return await self._db.get_login_history(user_id=user_id, params=params)
