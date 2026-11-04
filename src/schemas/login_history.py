from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, IPvAnyAddress


class LoginHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    login_at: datetime
    ip_address: IPvAnyAddress
    user_agent: str
