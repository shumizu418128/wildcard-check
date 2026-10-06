from typing import Literal, Protocol
from urllib.parse import parse_qs, urlparse

YoutubeAccess = Literal[
    "public", "unlisted", "private", "premiere", "unavailable", "unknown"
]


class YoutubeInspector(Protocol):
    def inspect(self, url: str) -> YoutubeAccess: ...


def youtube_video_id(url: str) -> str:
    text = url.strip()
    if text == "":
        return ""
    try:
        parsed = urlparse(text)
    except ValueError:
        return ""
    host = parsed.hostname or ""
    host = host.lower().removeprefix("www.")
    if host == "youtu.be":
        part = parsed.path.strip("/").split("/", 1)[0]
        return part if len(part) == 11 else ""
    if "youtube.com" not in host and "youtube-nocookie.com" not in host:
        return ""
    query_id = parse_qs(parsed.query).get("v", [""])[0]
    if len(query_id) == 11:
        return query_id
    parts = [part for part in parsed.path.split("/") if part]
    markers = {"embed", "shorts", "live", "v"}
    for index, part in enumerate(parts):
        if part in markers and index + 1 < len(parts) and len(parts[index + 1]) == 11:
            return parts[index + 1]
    return ""
