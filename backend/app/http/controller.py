import asyncio

from fastapi import (
    BackgroundTasks,
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
from app.http.presenter import present
from app.http.schema import AgreementRequest, ReviewResponse
from app.usecase.create_review import CreateReview
from app.usecase.gate_youtube import GateYoutube
from app.usecase.get_review import GetReview
from app.usecase.get_same_take_frame import GetSameTakeFrame
from app.usecase.record_agreement import RecordAgreement
from app.usecase.run_reviews import ReviewInput, RunReviews

# private / unlisted は即拒否。premiere は別扱い（ファイル追加提出）。
_BLOCKED_ACCESS: dict[YoutubeAccess, str] = {
    "private": "private_url",
    "unlisted": "unlisted_url",
}


def register(app: FastAPI) -> None:
    @app.get("/api/health")
    def health():
        return {"ok": True, "debug": debug_enabled()}

    @app.post("/api/reviews", status_code=201, response_model=ReviewResponse)
    async def create_review(
        request: Request,
        response: Response,
        background: BackgroundTasks,
        category: str = Form(...),
        source: str = Form(...),
        youtube_url: str = Form(""),
        raw_url: str = Form(""),
        file: UploadFile | None = File(None),
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
        if source_kind == "file" and file is None:
            raise HTTPException(status_code=400, detail="file")

        video: bytes | None = None
        if file is not None:
            video = await file.read()

        if source_kind == "youtube":
            # premiere 判定は yt-dlp のため時間がかかることがある。
            # その結果を、この POST のレスポンスで返す。
            gate: GateYoutube = request.app.state.gate_youtube
            access = await asyncio.to_thread(gate.execute, youtube_url)
            if access == "premiere":
                if video is None:
                    raise HTTPException(status_code=400, detail="premiere_unavailable")
                # 追加提出されたファイルで審査を続行する
                source_kind = "file"
            else:
                blocked = _BLOCKED_ACCESS.get(access)
                if blocked is not None:
                    raise HTTPException(status_code=400, detail=blocked)

        create: CreateReview = request.app.state.create_review
        run: RunReviews = request.app.state.run_reviews
        review = await asyncio.to_thread(
            create.execute, category, source_kind, youtube_url, raw_url
        )
        background.add_task(run.execute, ReviewInput(review, video))
        response.headers["Location"] = f"/api/reviews/{review.id}"
        return present(ReviewView(review, []))

    @app.get("/api/reviews/{review_id}", response_model=ReviewResponse)
    def read_review(review_id: str, request: Request):
        get_review: GetReview = request.app.state.get_review
        view = get_review.execute(review_id)
        if view is None:
            raise HTTPException(status_code=404, detail="job")
        return present(view)

    @app.get("/api/reviews/{review_id}/frames/{part}")
    def read_same_take_frame(review_id: str, part: str, request: Request):
        get_frame: GetSameTakeFrame = request.app.state.get_same_take_frame
        try:
            image = get_frame.execute(review_id, part)
        except RuntimeError as error:
            raise HTTPException(status_code=502, detail="frame") from error
        if image is None:
            raise HTTPException(status_code=404, detail="frame")
        return Response(
            content=image,
            media_type="image/jpeg",
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @app.post("/api/reviews/{review_id}/agreements", status_code=204)
    def create_agreement(review_id: str, body: AgreementRequest, request: Request):
        rule_id = body.rule_id.strip()
        if rule_id == "":
            raise HTTPException(status_code=400, detail="rule_id")
        record: RecordAgreement = request.app.state.record_agreement
        if not record.execute(review_id, rule_id):
            raise HTTPException(status_code=404, detail="job")
        return Response(status_code=204)
