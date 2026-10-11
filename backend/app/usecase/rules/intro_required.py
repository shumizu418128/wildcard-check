import logging

from app.domain.clips import ReviewClips
from app.domain.judge import Judge, is_yes, noul
from app.domain.media import MediaSource
from app.domain.review import Review
from app.domain.transcriber import Transcriber

logger = logging.getLogger(__name__)

INTRO_SECONDS = 30
LANGUAGE = "en"


class IntroRequired:
    id = "INTRO-REQUIRED"

    def __init__(self, media: MediaSource, transcriber: Transcriber) -> None:
        self.media = media
        self.transcriber = transcriber

    def applies(self, review: Review) -> bool:
        return True

    def evaluate(self, review: Review, clips: ReviewClips | None, judge: Judge) -> bool:
        """冒頭 30 秒の文字起こしで、挨拶か自己紹介をしていれば True。"""
        if clips is not None:
            audio = clips.intro_audio
        else:
            audio = self.media.audio(review, INTRO_SECONDS)
        transcript = self.transcriber.transcribe(audio, LANGUAGE).strip()
        logger.info(
            "intro whisper review_id=%s chars=%d text=%s",
            review.id,
            len(transcript),
            transcript,
        )
        if transcript == "":
            return False
        result = judge.decide(
            {
                "transcript": transcript,
                "category": review.category,
                "note": "Speech from the first 30 seconds of a beatbox wildcard video.",
            },
            {
                "intro": noul(
                    "Does the speaker greet the audience or introduce themselves, "
                    "for example 'My name is ..., and this is my ... wildcard'?"
                )
            },
        )
        passed = is_yes(result, "intro")
        logger.info(
            "intro decision review_id=%s passed=%s result=%s",
            review.id,
            passed,
            result,
        )
        return passed
