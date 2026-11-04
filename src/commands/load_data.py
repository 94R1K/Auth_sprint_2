from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission

from .fixtures.permissions import PERMISSIONS_FIXTURE
from .fixtures.roles import ROLES_FIXTURE

logger = logging.getLogger(__name__)


class LoadService:
    """Идемпотентная загрузка справочников (права + роли + связи)"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_permissions(self) -> int:
        """Загрузка прав. Возвращает кол-во обработанных записей"""
        if not PERMISSIONS_FIXTURE:
            return 0

        rows = [
            {"code": str(code), "name": desc, "is_system": True}
            for code, desc in PERMISSIONS_FIXTURE.items()
        ]
        stmt = pg_insert(Permission).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Permission.code],
            set_={"name": stmt.excluded.name},
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info("loaded permissions: %d", len(rows))
        return len(rows)

    async def load_roles(self) -> int:
        """Upsert ролей (без связей). Возвращает кол-во обработанных записей."""
        if not ROLES_FIXTURE:
            return 0

        rows = [
            {
                "name": r.name,
                "is_system": r.is_system,
            }
            for r in ROLES_FIXTURE
        ]
        stmt = pg_insert(Role).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Role.name],
            set_={
                "is_system": stmt.excluded.is_system,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info("loaded roles: %d", len(rows))
        return len(rows)

    async def load_role_permissions(self) -> int:
        """Связывает роли с правами (idempotent). Возвращает кол-во связей-кандидатов."""
        role_names = [r.name for r in ROLES_FIXTURE]
        all_codes = {str(c) for r in ROLES_FIXTURE for c in r.permission_codes}

        if not role_names or not all_codes:
            return 0

        roles_res = await self._session.execute(
            select(Role.id, Role.name).where(Role.name.in_(role_names))
        )
        role_id_by_name = {name: rid for rid, name in roles_res.all()}

        perms_res = await self._session.execute(
            select(Permission.id, Permission.code).where(Permission.code.in_(all_codes))
        )
        perm_id_by_code = {code: pid for pid, code in perms_res.all()}

        pairs: list[dict] = []
        for role_fixture in ROLES_FIXTURE:
            role_id = role_id_by_name.get(role_fixture.name)
            if role_id is None:
                logger.warning("Role '%s' not found after load_roles()", role_fixture.name)
                continue
            for code in role_fixture.permission_codes:
                perm_id = perm_id_by_code.get(str(code))
                if perm_id is None:
                    logger.warning("Permission '%s' not found after load_permissions()", code)
                    continue
                pairs.append({"role_id": role_id, "permission_id": perm_id})

        if not pairs:
            return 0

        stmt = pg_insert(RolePermission).values(pairs)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[RolePermission.role_id, RolePermission.permission_id]
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info("loaded role<->permission links: %d candidates", len(pairs))
        return len(pairs)

    async def load_all(self) -> None:
        """Полный цикл: права → роли → связи. Одна транзакция"""
        await self.load_permissions()
        await self.load_roles()
        await self.load_role_permissions()
        await self._session.commit()
        logger.info("load completed")
