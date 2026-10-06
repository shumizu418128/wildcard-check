from app.domain.judge import Judge
from app.domain.review import Review
from app.domain.youtube import YoutubeInspector


class GenVisibility:
    id = "GEN-VISIBILITY"

    def __init__(self, inspector: YoutubeInspector) -> None:
        self.inspector = inspector

    def applies(self, review: Review) -> bool:
        return review.source == "youtube"

    def evaluate(self, review: Review, video: bytes | None, judge: Judge) -> bool:
        """一般公開でダウンロードできれば True。プレミアはファイル追加提出に回すので True。"""
        return self.inspector.inspect(review.youtube_url) in ("public", "premiere")
