import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)

from app.domain.review import ReviewView, Source
from app.domain.youtube import YoutubeAccess
from app.gateway.config import debug_enabled
from app.http.clips import read_review_clips
from app.http.presenter import present
from app.http.schema import AgreementRequest, ReviewResponse
from app.usecase.create_review import CreateReview
from app.usecase.gate_youtube import GateYoutube
from app.usecase.get_review import GetReview
from app.usecase.record_agreement import RecordAgreement
from app.usecase.run_reviews import ReviewInput, RunReviews

# private / unlisted は即拒否
_BLOCKED_ACCESS: dict[YoutubeAccess, str] = {
    "private": "private_url",
    "unlisted": "unlisted_url",
}


def register(app: FastAPI, origin: Callable[..., Any]) -> None:
    # Render のヘルスチェックは秘密ヘッダーを付けられないので router に入れない
    @app.get("/api/health")
    def health():
        return {"ok": True, "debug": debug_enabled()}

    router = APIRouter(dependencies=[Depends(origin)])

    @router.post("/api/reviews", status_code=201, response_model=ReviewResponse)
    async def create_review(
        request: Request,
        response: Response,
        background: BackgroundTasks,
        category: str = Form(...),
        source: str = Form(...),
        youtube_url: str = Form(""),
        raw_url: str = Form(""),
        intro_audio: UploadFile | None = File(None),
        intro_frame: UploadFile | None = File(None),
        routine_frame: UploadFile | None = File(None),
    ):
        if source not in ("file", "youtube"):
            raise HTTPException(status_code=400, detail="source")
        source_kind: Source = "file" if source == "file" else "youtube"
        youtube_url = youtube_url.strip()
        raw_url = raw_url.strip()
        if source_kind == "youtube" and youtube_url == "":
            raise HTTPException(status_code=400, detail="youtube_url")
        if source_kind == "youtube" and raw_url == "":
            raise HTTPException(status_code=400, detail="raw_url")

        clips = await read_review_clips(intro_audio, intro_frame, routine_frame)

        if source_kind == "youtube":
            gate: GateYoutube = request.app.state.gate_youtube
            access = await asyncio.to_thread(gate.execute, youtube_url)
            blocked = _BLOCKED_ACCESS.get(access)
            if blocked is not None:
                raise HTTPException(status_code=400, detail=blocked)

        create: CreateReview = request.app.state.create_review
        run: RunReviews = request.app.state.run_reviews
        review = await asyncio.to_thread(
            create.execute, category, source_kind, youtube_url, raw_url
        )
        background.add_task(run.execute, ReviewInput(review, clips))
        response.headers["Location"] = f"/api/reviews/{review.id}"
        return present(ReviewView(review, []))

    @router.get("/api/reviews/{review_id}", response_model=ReviewResponse)
    def read_review(review_id: str, request: Request):
        get_review: GetReview = request.app.state.get_review
        view = get_review.execute(review_id)
        if view is None:
            raise HTTPException(status_code=404, detail="job")
        return present(view)

    @router.post("/api/reviews/{review_id}/agreements", status_code=204)
    def create_agreement(review_id: str, body: AgreementRequest, request: Request):
        rule_id = body.rule_id.strip()
        if rule_id == "":
            raise HTTPException(status_code=400, detail="rule_id")
        record: RecordAgreement = request.app.state.record_agreement
        if not record.execute(review_id, rule_id):
            raise HTTPException(status_code=404, detail="job")
        return Response(status_code=204)

    app.include_router(router)
