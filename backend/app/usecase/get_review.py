from app.domain.review import ReviewView, RuleResult
from app.domain.review_repository import ReviewRepository
from app.usecase.rule import Rule


class GetReview:
    def __init__(self, repository: ReviewRepository, rules: tuple[Rule, ...]) -> None:
        self.repository = repository
        self.rules = rules

    def execute(self, review_id: str) -> ReviewView | None:
        found = self.repository.get(review_id)
        if found is None:
            return None
        review, results = found
        agreements = (
            self.repository.agreements(review_id) if review.source == "youtube" else []
        )
        if review.status != "done":
            return ReviewView(review, [], agreements)
        by_id = {item.rule_id: item.ok for item in results}
        ordered = [
            RuleResult(rule.id, by_id[rule.id])
            for rule in self.rules
            if rule.applies(review)
        ]
        return ReviewView(review, ordered, agreements)
