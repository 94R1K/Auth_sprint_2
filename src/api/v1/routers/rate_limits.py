from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    limit: int
    window: int
