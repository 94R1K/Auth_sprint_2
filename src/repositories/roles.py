from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.dto import RolesServiceParams
from core.exceptions import ConflictError, NotFoundError
from core.repositories import RoleRepositoryABC
from models import Permission, Role, RolePermission, User, UserRole
from schemas import RoleCreate, RoleRead, RoleUpdate


class RoleRepository(RoleRepositoryABC):
    def __init__(self, db: AsyncSession):
        self._session = db

    async def get_roles(self, params: RolesServiceParams) -> list[RoleRead]:
        """Получить список ролей"""
        query = select(Role)
        if params.limit is not None:
            query = query.limit(params.limit)
        if params.offset is not None:
            query = query.offset(params.offset)
        if params.name:
            query = query.where(Role.name.icontains(params.name))
        if params.is_system is not None:
            query = query.where(Role.is_system == params.is_system)

        roles = await self._session.execute(query)
        return [RoleRead.model_validate(role) for role in roles.scalars().all()]

    async def get_role_by_id(self, role_id: UUID) -> RoleRead:
        """Получить роль по идентификатору"""
        role = await self._session.get(Role, role_id)
        return RoleRead.model_validate(role) if role else None
    
    async def get_role_by_name(self, role_name: str) -> RoleRead:
        query = select(Role).where(Role.name==role_name)
        role = await self._session.scalar(query)
        return role

    async def create_role(self, role: RoleCreate) -> RoleRead:
        """Создать роль"""
        created_role = Role(**role.model_dump())
        self._session.add(created_role)
        try:
            await self._session.flush()
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            if getattr(e.orig, "sqlstate", None) == "23505":
                raise ConflictError(
                    f"Role with name '{role.name}' already exists"
                ) from e
        print(created_role)
        return RoleRead(
            id=created_role.id,
            name=created_role.name,
            created_at=created_role.created_at,
            is_system=created_role.is_system,
            permissions=[],   
        )

    async def update_role_by_id(self, role_id: UUID, role_to_update: RoleUpdate) -> RoleRead:
        """Обновить роль по идентификатору"""
        role = await self._session.get(Role, role_id)
        if role is None:
            return None
        
        for field, value in role_to_update.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        try:
            await self._session.flush()
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            if getattr(e.orig, "sqlstate", None) == "23505":
                raise ConflictError(
                    f"Role with name '{role_to_update.name}' already exists"
                ) from e
            raise
        
        return RoleRead.model_validate(role)

    async def delete_role_by_id(self, role_id: UUID) -> bool:
        """Удалить роль по идентификатору"""
        role = await self._session.get(Role, role_id)
        if not role:
            return False
        await self._session.delete(role)
        await self._session.flush()
        await self._session.commit()
        return True
    
    async def add_permissions_to_role(
        self, role_id: UUID, permission_codes: list[str]
    ) -> RoleRead:
        role = await self._session.get(Role, role_id)
        if role is None:
            raise NotFoundError(f"Role {role_id} not found")

        if not permission_codes:
            return await self._get_role_with_permissions(role_id)

        perms_res = await self._session.execute(
            select(Permission.id, Permission.code).where(
                Permission.code.in_(permission_codes)
            )
        )
        found: dict[str, UUID] = {code: pid for pid, code in perms_res.all()}
        missing = set(permission_codes) - found.keys()
        if missing:
            raise NotFoundError(f"Permissions not found: {sorted(missing)}")

        target_ids = list(found.values())
        existing_res = await self._session.execute(
            select(RolePermission.permission_id).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(target_ids),
            )
        )
        existing_ids: set[UUID] = {row[0] for row in existing_res.all()}

        new_links = [
            RolePermission(role_id=role_id, permission_id=pid)
            for pid in target_ids
            if pid not in existing_ids
        ]
        if new_links:
            self._session.add_all(new_links)

        await self._session.flush()
        await self._session.commit()
        return await self.get_role_by_id(role_id)

    async def remove_permission_from_role(
        self, role_id: UUID, permission_id: UUID
    ) -> RoleRead:
        role = await self._session.get(Role, role_id)
        if role is None:
            raise NotFoundError(f"Role {role_id} not found")

        exists = await self._session.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        if exists.scalar_one_or_none() is None:
            raise NotFoundError(
                f"Permission {permission_id} is not assigned to role {role_id}"
            )

        await self._session.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        await self._session.flush()
        await self._session.commit()
        return await self.get_role_by_id(role_id)

    async def assign_role_to_user(self, role_id: UUID, user_id: UUID) -> None:
        user = await self._session.get(User, user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        role = await self._session.get(Role, role_id)
        if not role:
            raise NotFoundError(f"Role {role_id} not found")

        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none():
            return

        new_link = UserRole(user_id=user_id, role_id=role_id)
        self._session.add(new_link)
        await self._session.flush()
        await self._session.commit()

    async def remove_role_from_user(self, role_id: UUID, user_id: UUID) -> None:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )
        result = await self._session.execute(stmt)
        link = result.scalar_one_or_none()
        
        if not link:
            raise NotFoundError(f"Role {role_id} is not assigned to user {user_id}")

        await self._session.delete(link)
        await self._session.flush()
        await self._session.commit()


    async def get_roles_by_user_id(self, user_id: UUID) -> list[RoleRead]:
        query = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self._session.execute(query)

        roles = result.scalars().all()

        return [RoleRead.model_validate(role) for role in roles]
