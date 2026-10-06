from dataclasses import dataclass, field
from typing import Literal

Source = Literal["file", "youtube"]
ReviewStatus = Literal["running", "done"]


@dataclass
class Review:
    id: str
    category: str
    source: Source
    youtube_url: str
    raw_url: str
    status: ReviewStatus


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    ok: bool


@dataclass
class ReviewView:
    review: Review
    results: list[RuleResult]
    agreements: list[str] = field(default_factory=list)
