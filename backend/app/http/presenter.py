from app.domain.review import ReviewView
from app.http.schema import ReviewResponse, RuleResponse


def present(view: ReviewView) -> ReviewResponse:
    return ReviewResponse(
        id=view.review.id,
        category=view.review.category,
        source=view.review.source,
        status=view.review.status,
        rules=[
            RuleResponse(id=item.rule_id, status="clear" if item.ok else "fix")
            for item in view.results
        ],
        raw_url=view.review.raw_url,
        youtube_url=view.review.youtube_url,
        agreements=view.agreements,
    )
