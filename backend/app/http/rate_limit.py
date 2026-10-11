import math
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from limits import RateLimitItem
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter

review_path = "/api/reviews"


def limit_reviews(app: FastAPI, item: RateLimitItem) -> None:
    """審査の作成だけを IP ごとに制限する。2xx で終わった送信だけを数える。"""
    limiter = MovingWindowRateLimiter(MemoryStorage())

    @app.middleware("http")
    async def limit(request: Request, call_next):
        if request.method != "POST" or request.url.path != review_path:
            return await call_next(request)
        key = request.client.host if request.client else ""
        if not await limiter.test(item, key):
            stats = await limiter.get_window_stats(item, key)
            wait = max(1, math.ceil(stats.reset_time - time.time()))
            return JSONResponse(
                {"detail": "rate_limited"},
                status_code=429,
                headers={"Retry-After": str(wait)},
            )
        response = await call_next(request)
        if 200 <= response.status_code < 300:
            await limiter.hit(item, key)
        return response
