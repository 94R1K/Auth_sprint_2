from .params import LimitOffsetParams


class RolesServiceParams(LimitOffsetParams):
    name: str | None = None
    is_system: str | None = None
