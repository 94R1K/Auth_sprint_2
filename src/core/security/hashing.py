import hashlib
import hmac
from uuid import UUID

from core.config import settings


def hash_rate_limit_value(value: str | UUID) -> str:
    if isinstance(value, UUID):
        value = str(value)

    return hmac.new(
        key=settings.rate_limit_secret.get_secret_value().encode(),
        msg=value.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
