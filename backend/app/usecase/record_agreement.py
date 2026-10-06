from app.domain.review_repository import ReviewRepository


class RecordAgreement:
    """YouTube チェックの同意だけを保存する。ファイルは復帰できないため残さない。"""

    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def execute(self, review_id: str, rule_id: str) -> bool:
        found = self.repository.get(review_id)
        if found is None:
            return False
        review, _ = found
        if review.source != "youtube":
            return False
        self.repository.save_agreement(review_id, rule_id)
        return True
