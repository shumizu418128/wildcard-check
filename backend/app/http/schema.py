from typing import Literal

from pydantic import BaseModel

from app.domain.review import Source


class RuleResponse(BaseModel):
    id: str
    status: Literal["clear", "fix"]


class ReviewResponse(BaseModel):
    id: str
    category: str
    source: Source
    status: Literal["running", "done"]
    rules: list[RuleResponse]
    raw_url: str = ""
    youtube_url: str = ""
    agreements: list[str] = []


class AgreementRequest(BaseModel):
    rule_id: str
