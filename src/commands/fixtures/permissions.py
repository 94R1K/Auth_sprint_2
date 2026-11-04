from core.permissions import PermissionCode

# code -> description
PERMISSIONS_FIXTURE: dict[PermissionCode, str] = {
    # movies
    PermissionCode.MOVIE_READ:        "Просмотр фильмов",
    PermissionCode.MOVIE_RECENT_READ: "Доступ к недавно вышедшим фильмам (ETL)",
    # roles
    PermissionCode.ROLES_READ:        "Просмотр списка ролей",
    PermissionCode.ROLES_CREATE:      "Создание ролей",
    PermissionCode.ROLES_UPDATE:      "Редактирование ролей",
    PermissionCode.ROLES_DELETE:      "Удаление ролей",
    # users
    PermissionCode.USERS_READ:        "Просмотр списка пользователей",
    PermissionCode.USERS_ASSIGN_ROLE: "Назначение ролей пользователям",
    # permissions (справочник прав)
    PermissionCode.PERMISSIONS_READ:  "Просмотр справочника прав",
}
