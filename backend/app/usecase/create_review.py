from uuid import uuid7

from app.domain.review import Review, Source
from app.domain.review_repository import ReviewRepository


class CreateReview:
    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def execute(
        self, category: str, source: Source, youtube_url: str, raw_url: str
    ) -> Review:
        review = Review(
            id=str(uuid7()),
            category=category,
            source=source,
            youtube_url=youtube_url,
            raw_url=raw_url,
            status="running",
        )
        self.repository.add(review)
        return review
