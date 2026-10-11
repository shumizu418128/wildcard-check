from contextlib import asynccontextmanager

from fastapi import FastAPI
from limits import parse
from app.gateway.clef import ClefJudge
from app.gateway.config import origin_secret, require_supabase
from app.gateway.ffmpeg_media import FfmpegMedia
from app.gateway.groq_whisper import GroqWhisper
from app.gateway.supabase_review_repository import SupabaseReviewRepository
from app.gateway.yt_dlp_youtube import YtDlpYoutubeInspector
from app.http.controller import register
from app.http.origin import require_origin
from app.http.rate_limit import limit_reviews
from app.usecase.create_review import CreateReview
from app.usecase.gate_youtube import GateYoutube
from app.usecase.get_review import GetReview
from app.usecase.get_same_take_frame import GetSameTakeFrame
from app.usecase.record_agreement import RecordAgreement
from app.usecase.rules.catalog import build_rules
from app.usecase.run_reviews import RunReviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    require_supabase()
    repository = SupabaseReviewRepository()
    inspector = YtDlpYoutubeInspector()
    media = FfmpegMedia()
    rules = build_rules(inspector, media, GroqWhisper())
    app.state.create_review = CreateReview(repository)
    app.state.get_review = GetReview(repository, rules)
    app.state.get_same_take_frame = GetSameTakeFrame(repository, media)
    app.state.record_agreement = RecordAgreement(repository)
    app.state.gate_youtube = GateYoutube(inspector)
    app.state.run_reviews = RunReviews(repository, ClefJudge(), rules)
    yield


secret = origin_secret()
# 秘密ヘッダーの照合はルートにしか効かないので、本番ではドキュメントを出さない
docs = secret == ""
app = FastAPI(
    title="Wildcard review",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if docs else None,
    redoc_url="/redoc" if docs else None,
    openapi_url="/openapi.json" if docs else None,
)
limit_reviews(app, parse("1 per 10 seconds"))
register(app, require_origin(secret))
