from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.gateway.clef import ClefJudge
from app.gateway.config import require_supabase
from app.gateway.ffmpeg_media import FfmpegMedia
from app.gateway.groq_whisper import GroqWhisper
from app.gateway.jev import JevJudge
from app.gateway.supabase_review_repository import SupabaseReviewRepository
from app.gateway.yt_dlp_youtube import YtDlpYoutubeInspector
from app.http.controller import register
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
    rules = build_rules(inspector, media, GroqWhisper(), JevJudge())
    app.state.create_review = CreateReview(repository)
    app.state.get_review = GetReview(repository, rules)
    app.state.get_same_take_frame = GetSameTakeFrame(repository, media)
    app.state.record_agreement = RecordAgreement(repository)
    app.state.gate_youtube = GateYoutube(inspector)
    app.state.run_reviews = RunReviews(repository, ClefJudge(), rules)
    yield


app = FastAPI(title="Wildcard review", version="1.0.0", lifespan=lifespan)
register(app)
