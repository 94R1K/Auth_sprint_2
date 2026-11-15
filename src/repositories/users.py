from typing import TYPE_CHECKING
from uuid import UUID

from core.dto import LimitOffsetParams
from core.exceptions import ConflictError, NotFoundError
from core.repositories import UserRepositoryABC
from core.security import hash_password, verify_password_and_update
from models import LoginHistory, User
from schemas import LoginHistoryRead, UserInDB, UserRead, UserUpdate
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


if TYPE_CHECKING:
    from schemas import UserCreate


class UserRepository(UserRepositoryABC):
    def __init__(self, db: AsyncSession):
        self._session = db

    async def create_user(self, user: UserCreate) -> UserInDB:
        db_user: User = User(
            login=user.login,
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        self._session.add(db_user)
        try:
            await self._session.commit()
            await self._session.refresh(db_user)
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(
                f"Пользователь с логином {user.login} уже существует"
            ) from exc

        return UserInDB.model_validate(db_user)

    async def update_password_hash(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(password=password_hash)
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def get_user_by_id(self, user_id: UUID) -> User:
        user: User | None = await self._session.get(User, user_id)

        if not user:
            raise NotFoundError("Пользователь не найден")

        return user

    async def get_user_by_login(self, login: str) -> User:
        stmt = select(User).where(User.login == login)
        user: User | None = await self._session.scalar(stmt)

        if not user:
            raise NotFoundError("Пользователь не найден")

        return user

    async def update_me(
        self, user_id: UUID, new_user_data: UserUpdate
    ) -> UserRead | None:
        user: User | None = await self._session.get(User, user_id)
        if user:
            if new_user_data.first_name is not None:
                user.first_name = new_user_data.first_name
            if new_user_data.last_name is not None:
                user.last_name = new_user_data.last_name
            if new_user_data.login is not None:
                query = select(User).where(
                    User.login == new_user_data.login,
                    User.id != user_id  # Исключаем самих себя
                )
                existing = await self._session.scalar(query)
                if existing and existing.id != user_id:
                    raise ConflictError("Введенный логин уже занят")

                user.login = new_user_data.login

            if new_user_data.password is not None:
                is_valid, _ = await verify_password_and_update(new_user_data.password.current_password, user.password)
                if not is_valid:
                    raise ConflictError("Current password is incorrect")
                user.password = await hash_password(new_user_data.password.new_password)

            try:
                await self._session.commit()
            except IntegrityError as e:
                await self._session.rollback()
                if getattr(e.orig, "sqlstate", None) == "23505":
                    raise ConflictError("Введенный логин уже занят") from e
                raise

        return UserRead.model_validate(user) if user else None

    async def create_login_history(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        history_entry = LoginHistory(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(history_entry)
        await self._session.commit()

    async def get_login_history(
        self, user_id: UUID, params: LimitOffsetParams
    ) -> list[LoginHistoryRead]:
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)
        if params.limit is not None and params.limit is not None:
            query = query.limit(params.limit).offset(params.offset)

        query = query.order_by(LoginHistory.login_at, LoginHistory.id)

        login_history_list = await self._session.execute(query)

        return [
            LoginHistoryRead.model_validate(item)
            for item in login_history_list.scalars().all()
        ]
