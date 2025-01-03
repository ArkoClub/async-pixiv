from typing import NoReturn

from aiolimiter import AsyncLimiter

__all__ = ("RateLimiter",)


class RateLimiter(AsyncLimiter):
    max_rate: float | None

    def __init__(
        self, max_rate: float | None = 100.0, time_period: float = 60
    ) -> NoReturn:
        if max_rate is not None:
            super().__init__(max_rate, time_period)
        else:
            self.max_rate = max_rate

    async def acquire(self, amount: float = 1) -> None:
        if self.max_rate is not None:
            await super().acquire(amount)
