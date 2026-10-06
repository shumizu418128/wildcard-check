import threading
from typing import TypeGuard

from supabase import create_client

from app.domain.review import Review, RuleResult, Source
from app.gateway.config import supabase_credentials


class SupabaseReviewRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._client = None

    def _db(self):
        if self._client is None:
            url, key = supabase_credentials()
            self._client = create_client(url, key)
        return self._client

    def add(self, review: Review) -> None:
        with self._lock:
            self._db().table("reviews").insert(
                {
                    "id": review.id,
                    "category": review.category,
                    "source": review.source,
                    "youtube_url": review.youtube_url,
                    "raw_url": review.raw_url,
                    "status": review.status,
                }
            ).execute()

    def save_result(self, review_id: str, rule_id: str, ok: bool) -> None:
        with self._lock:
            self._db().table("review_results").insert(
                {"review_id": review_id, "rule_id": rule_id, "ok": ok}
            ).execute()

    def mark_done(self, review_id: str) -> None:
        with self._lock:
            self._db().table("reviews").update({"status": "done"}).eq(
                "id", review_id
            ).execute()

    def get(self, review_id: str) -> tuple[Review, list[RuleResult]] | None:
        with self._lock:
            job_response = (
                self._db()
                .table("reviews")
                .select("*")
                .eq("id", review_id)
                .limit(1)
                .execute()
            )
            jobs = object_rows(job_response.data)
            if len(jobs) == 0:
                return None
            result_response = (
                self._db()
                .table("review_results")
                .select("rule_id, ok")
                .eq("review_id", review_id)
                .execute()
            )
            results = object_rows(result_response.data)
        return to_review(jobs[0]), [to_result(row) for row in results]

    def save_agreement(self, review_id: str, rule_id: str) -> None:
        with self._lock:
            self._db().table("review_agreements").upsert(
                {"review_id": review_id, "rule_id": rule_id},
                on_conflict="review_id,rule_id",
                ignore_duplicates=True,
            ).execute()

    def agreements(self, review_id: str) -> list[str]:
        with self._lock:
            response = (
                self._db()
                .table("review_agreements")
                .select("rule_id")
                .eq("review_id", review_id)
                .order("created_at")
                .execute()
            )
        return [str(row["rule_id"]) for row in object_rows(response.data)]


def is_object_row(value: object) -> TypeGuard[dict]:
    return isinstance(value, dict)


def object_rows(data: list | None) -> list[dict]:
    if data is None:
        return []
    return [row for row in data if is_object_row(row)]


def to_review(row: dict) -> Review:
    source: Source = "youtube" if row["source"] == "youtube" else "file"
    return Review(
        id=str(row["id"]),
        category=row["category"],
        source=source,
        youtube_url=row.get("youtube_url", ""),
        raw_url=row.get("raw_url", ""),
        status="done" if row["status"] == "done" else "running",
    )


def to_result(row: dict) -> RuleResult:
    return RuleResult(rule_id=row["rule_id"], ok=bool(row["ok"]))
