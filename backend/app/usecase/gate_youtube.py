from app.domain.youtube import YoutubeAccess, YoutubeInspector


class GateYoutube:
    """YouTube URL がレビュー開始可能かを判定する。

    premiere 判定は yt-dlp のため時間がかかることがある。
    呼び出し側は、その結果を最初の POST /api/reviews レスポンスで返す。
    """

    def __init__(self, inspector: YoutubeInspector) -> None:
        self.inspector = inspector

    def execute(self, youtube_url: str) -> YoutubeAccess:
        return self.inspector.inspect(youtube_url)
