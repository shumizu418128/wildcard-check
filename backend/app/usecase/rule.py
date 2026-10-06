from typing import Protocol

from app.domain.judge import Judge
from app.domain.review import Review


class Rule(Protocol):
    id: str

    def applies(self, review: Review) -> bool: ...

    def evaluate(self, review: Review, video: bytes | None, judge: Judge) -> bool: ...
