from app.domain.youtube import YoutubeAccess, YoutubeInspector


class GateYoutube:
    """YouTube URL がレビュー開始可能かを判定する。"""

    def __init__(self, inspector: YoutubeInspector) -> None:
        self.inspector = inspector

    def execute(self, youtube_url: str) -> YoutubeAccess:
        return self.inspector.inspect(youtube_url)
