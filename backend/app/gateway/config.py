import base64
import json
import os
from pathlib import Path

url_env = "SUPABASE_URL"
key_env = "SUPABASE_KEY"
origin_env = "ORIGIN_SECRET"
youtube_key_env = "YOUTUBE_API_KEY"


def load_env() -> None:
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text == "" or text.startswith("#") or "=" not in text:
            continue
        name, value = text.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def require_supabase() -> None:
    load_env()
    if (
        os.environ.get(url_env, "").strip() == ""
        or os.environ.get(key_env, "").strip() == ""
    ):
        raise RuntimeError("supabase")
    key = os.environ[key_env].strip()
    if is_public_supabase_key(key):
        raise RuntimeError(
            "SUPABASE_KEY には publishable/anon ではなく "
            "secret/service_role キーを設定してください"
        )


def is_public_supabase_key(key: str) -> bool:
    if key.startswith("sb_publishable_"):
        return True
    if key.startswith("sb_secret_"):
        return False
    return jwt_role(key) == "anon"


def jwt_role(key: str) -> str | None:
    parts = key.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    pad = "=" * (-len(payload) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload + pad)
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    role = data.get("role")
    return role if isinstance(role, str) else None


def supabase_credentials() -> tuple[str, str]:
    require_supabase()
    return os.environ[url_env].strip(), os.environ[key_env].strip()


def origin_secret() -> str:
    load_env()
    return os.environ.get(origin_env, "").strip()


def youtube_api_key() -> str:
    load_env()
    return os.environ.get(youtube_key_env, "").strip()


def debug_enabled() -> bool:
    load_env()
    value = os.environ.get("debug", "").strip().lower()
    return value in ("1", "true", "yes", "on")
