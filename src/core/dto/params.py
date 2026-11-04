from typing import Annotated

from pydantic import BaseModel, Field


class LimitOffsetParams(BaseModel):
    limit: Annotated[int, Field(default=50, ge=1, le=100)]
    offset: Annotated[int, Field(ge=0, default=0)]
