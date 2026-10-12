import time
from collections.abc import Mapping
from typing import Any

import requests

from app.domain.youtube import YoutubeAccess, youtube_video_id
from app.gateway.config import youtube_api_key
from app.gateway.debug import debug_fixture_access, debug_gate_delay

VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
TIMEOUT_SECONDS = 10
_PRIVACY: dict[str, YoutubeAccess] = {
    "public": "public",
    "unlisted": "unlisted",
    "private": "private",
}


class YoutubeDataApiInspector:
    def inspect(self, url: str) -> YoutubeAccess:
        fixture = debug_fixture_access(url)
        if fixture is not None:
            time.sleep(debug_gate_delay())
            return fixture
        video_id = youtube_video_id(url)
        key = youtube_api_key()
        if video_id == "" or key == "":
            return "unknown"
        try:
            response = requests.get(
                VIDEOS_URL,
                params={"part": "status", "id": video_id, "key": key},
                timeout=TIMEOUT_SECONDS,
            )
        except requests.RequestException:
            return "unknown"
        if not response.ok:
            return "unknown"
        try:
            payload = response.json()
        except ValueError:
            return "unknown"
        return self._from_payload(payload)

    def _from_payload(self, payload: Any) -> YoutubeAccess:
        if not isinstance(payload, Mapping):
            return "unknown"
        items = payload.get("items")
        if not isinstance(items, list):
            return "unknown"
        # 他人の非公開動画と削除済みの動画は、どちらも items が空で返る
        if len(items) == 0:
            return "private"
        item = items[0]
        status = item.get("status") if isinstance(item, Mapping) else None
        privacy = status.get("privacyStatus") if isinstance(status, Mapping) else None
        return _PRIVACY.get(privacy, "unknown") if isinstance(privacy, str) else "unknown"
