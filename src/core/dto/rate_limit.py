from pydantic import BaseModel, ConfigDict, Field


class RateLimitRule(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    key: str = Field(min_length=1)
    limit: int = Field(gt=0)
    window: int = Field(gt=0)
