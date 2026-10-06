from urllib.parse import urlparse

import requests

from app.domain.judge import Judge
from app.domain.review import Review
from app.domain.youtube import youtube_video_id


class GenYoutube:
    id = "GEN-YOUTUBE"

    def applies(self, review: Review) -> bool:
        return review.source == "youtube"

    def evaluate(self, review: Review, video: bytes | None, judge: Judge) -> bool:
        """通常の YouTube 動画なら True。/shorts/ で開き、/shorts/ のまま残れば Shorts。"""
        video_id = youtube_video_id(review.youtube_url)
        if video_id == "":
            return False
        response = requests.get(
            f"https://www.youtube.com/shorts/{video_id}",
            allow_redirects=True,
            timeout=30,
        )
        return not urlparse(response.url).path.startswith("/shorts/")
