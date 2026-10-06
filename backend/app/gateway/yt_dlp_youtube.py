from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

import yt_dlp
from yt_dlp.utils import YoutubeDLError

from app.domain.youtube import YoutubeAccess
from app.gateway.debug import debug_fixture_access

if TYPE_CHECKING:
    from yt_dlp import _Params


class YtDlpYoutubeInspector:
    def inspect(self, url: str) -> YoutubeAccess:
        fixture = debug_fixture_access(url)
        if fixture is not None:
            return fixture
        # typeshed の skip_download は str なので、bool を渡すために cast する
        ydl_opts: _Params = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": cast(Any, True),
            "extract_flat": False,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except YoutubeDLError as error:
            return self._from_error(str(error))

        if not isinstance(info, dict):
            return "unknown"
        return self._from_info(info)

    def _from_info(self, info: Mapping[str, Any]) -> YoutubeAccess:
        live_status = info.get("live_status")
        if live_status == "is_upcoming":
            return "premiere"

        availability = info.get("availability")
        if availability == "private":
            return "private"
        if availability == "unlisted":
            return "unlisted"
        if availability == "needs_auth":
            return "private"
        if availability in ("public", "premium_only", None):
            return "public" if self._downloadable(info) else "unavailable"
        return "unknown"

    def _downloadable(self, info: Mapping[str, Any]) -> bool:
        """DRM なしで映像か音声を取れるフォーマットがあるか。"""
        formats = info.get("formats") or []
        return any(
            isinstance(item, Mapping)
            and not item.get("has_drm")
            and (item.get("vcodec") != "none" or item.get("acodec") != "none")
            for item in formats
        )

    def _from_error(self, message: str) -> YoutubeAccess:
        text = message.lower()
        if "private" in text:
            return "private"
        if "premiere" in text or "live event will begin" in text:
            return "premiere"
        return "unknown"
