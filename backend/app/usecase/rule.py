from typing import Protocol

from app.domain.clips import ReviewClips
from app.domain.judge import Judge
from app.domain.review import Review


class Rule(Protocol):
    id: str

    def applies(self, review: Review) -> bool: ...

    def evaluate(self, review: Review, clips: ReviewClips, judge: Judge) -> bool: ...
