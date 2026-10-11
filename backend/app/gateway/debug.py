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


def debug_fixture_access(url: str) -> YoutubeAccess | None:
    """debug 時のみ、フィクスチャ URL の想定アクセスを返す。"""
    if not debug_enabled():
        return None
    return _DEBUG_ACCESS.get(youtube_video_id(url))


def is_debug_short_fixture(url: str) -> bool:
    """ゲートは通すが NO-SHORT を落とす Shorts フィクスチャか。"""
    return debug_enabled() and youtube_video_id(url) == SHORT_VIDEO_ID
