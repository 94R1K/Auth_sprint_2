from .params import LimitOffsetParams


class PermissionsServiceParams(LimitOffsetParams):
    code: str | None = None
    name: str | None = None
    is_system: str | None = None
