import hmac

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

header = "x-origin-secret"
# Render のヘルスチェックはヘッダーを付けられない
open_paths = frozenset({"/api/health"})


def guard(app: FastAPI, secret: str) -> None:
    """Vercel が付ける秘密ヘッダーのないリクエストを拒否する。secret が空なら素通しする。"""
    if secret == "":
        return
    expected = secret.encode()

    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        if request.url.path in open_paths:
            return await call_next(request)
        given = request.headers.get(header, "").encode()
        if not hmac.compare_digest(given, expected):
            return JSONResponse({"detail": "forbidden"}, status_code=403)
        return await call_next(request)
