import random

from app.domain.youtube import YoutubeAccess, youtube_video_id
from app.gateway.config import debug_enabled

# debug=true のときだけ使うフィクスチャ動画 ID
SHORT_VIDEO_ID = "SHORT-VIDEO"
PREMIERE_VIDEO_ID = "PREMIRE-VID"
PRIVATE_VIDEO_ID = "PRIVATE-VID"

_DEBUG_ACCESS: dict[str, YoutubeAccess] = {
    SHORT_VIDEO_ID: "public",
    PREMIERE_VIDEO_ID: "premiere",
    PRIVATE_VIDEO_ID: "private",
}

# 実際の処理時間を再現する待機秒数の範囲
_GATE_DELAY = (1.0, 3.0)
_RULE_DELAY = (0.5, 1.5)


def debug_fixture_access(url: str) -> YoutubeAccess | None:
    """debug 時のみ、フィクスチャ URL の想定アクセスを返す。"""
    if not debug_enabled():
        return None
    return _DEBUG_ACCESS.get(youtube_video_id(url))


def is_debug_fixture(url: str) -> bool:
    """debug 時のみ、審査でネットワークに出さないフィクスチャ URL か。"""
    return debug_enabled() and youtube_video_id(url) in _DEBUG_ACCESS


def is_debug_short_fixture(url: str) -> bool:
    """ゲートは通すが NO-SHORT を落とす Shorts フィクスチャか。"""
    return debug_enabled() and youtube_video_id(url) == SHORT_VIDEO_ID


def debug_gate_delay() -> float:
    """yt-dlp 判定の代わりに待つ秒数。"""
    return random.uniform(*_GATE_DELAY)


def debug_rule_delay() -> float:
    """ルール 1 件の審査の代わりに待つ秒数。"""
    return random.uniform(*_RULE_DELAY)
