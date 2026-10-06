from app.domain.media import MediaSource
from app.domain.review_repository import ReviewRepository
from app.usecase.rules.intro_same_take import INTRO_SECONDS, ROUTINE_SECONDS

FRAME_SECONDS = {"intro": INTRO_SECONDS, "routine": ROUTINE_SECONDS}


class GetSameTakeFrame:
    def __init__(self, repository: ReviewRepository, media: MediaSource) -> None:
        self.repository = repository
        self.media = media

    def execute(self, review_id: str, part: str) -> bytes | None:
        """INTRO-SAME-TAKE が見たコマを返す。ファイル提出は動画を保持しないので None。"""
        seconds = FRAME_SECONDS.get(part)
        if seconds is None:
            return None
        found = self.repository.get(review_id)
        if found is None:
            return None
        review, _ = found
        if review.source != "youtube":
            return None
        return self.media.frame(review, None, seconds)
