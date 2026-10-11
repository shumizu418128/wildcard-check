import asyncio
from dataclasses import dataclass

from app.domain.judge import Judge
from app.domain.review import Review
from app.domain.review_repository import ReviewRepository
from app.gateway.debug import (
    debug_rule_delay,
    is_debug_fixture,
    is_debug_short_fixture,
)
from app.usecase.rule import Rule


@dataclass
class ReviewInput:
    review: Review
    video: bytes | None


class RunReviews:
    def __init__(
        self, repository: ReviewRepository, judge: Judge, rules: tuple[Rule, ...]
    ) -> None:
        self.repository = repository
        self.judge = judge
        self.rules = rules

    async def execute(self, review_input: ReviewInput) -> None:
        review = review_input.review
        try:
            if review.source == "youtube" and is_debug_fixture(review.youtube_url):
                await self._save_debug_fixture(review)
                return
            for rule in self.rules:
                if not rule.applies(review):
                    continue
                ok = await asyncio.to_thread(
                    rule.evaluate, review, review_input.video, self.judge
                )
                await asyncio.to_thread(
                    self.repository.save_result, review.id, rule.id, ok
                )
            await asyncio.to_thread(self.repository.mark_done, review.id)
        finally:
            review_input.video = None

    async def _save_debug_fixture(self, review: Review) -> None:
        """フィクスチャは実動画がないため審査を模擬する。SHORT-VIDEO だけ NO-SHORT を失敗させる。"""
        short = is_debug_short_fixture(review.youtube_url)
        for rule in self.rules:
            if not rule.applies(review):
                continue
            await asyncio.sleep(debug_rule_delay())
            ok = not (short and rule.id == "NO-SHORT")
            await asyncio.to_thread(self.repository.save_result, review.id, rule.id, ok)
        await asyncio.to_thread(self.repository.mark_done, review.id)
