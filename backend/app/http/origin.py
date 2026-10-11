import secrets
from collections.abc import Callable

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

header = "x-origin-secret"
scheme = APIKeyHeader(name=header, auto_error=False)


def require_origin(secret: str) -> Callable[[str | None], None]:
    """Vercel が付ける秘密ヘッダーを照合する依存関数を返す。secret が空なら素通しする。"""

    def check(given: str | None = Security(scheme)) -> None:
        if secret == "":
            return
        if given is None or not secrets.compare_digest(given.encode(), secret.encode()):
            raise HTTPException(status_code=403, detail="forbidden")

    return check
