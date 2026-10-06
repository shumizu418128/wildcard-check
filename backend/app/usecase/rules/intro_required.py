from app.domain.judge import Judge, is_yes, noul
from app.domain.media import MediaSource
from app.domain.review import Review
from app.domain.transcriber import Transcriber

INTRO_SECONDS = 30
LANGUAGE = "en"


class IntroRequired:
    id = "INTRO-REQUIRED"

    def __init__(
        self, media: MediaSource, transcriber: Transcriber, jev: Judge
    ) -> None:
        self.media = media
        self.transcriber = transcriber
        self.jev = jev

    def applies(self, review: Review) -> bool:
        return True

    def evaluate(self, review: Review, video: bytes | None, judge: Judge) -> bool:
        """冒頭 30 秒の文字起こしで、挨拶か自己紹介をしていれば True。"""
        audio = self.media.audio(review, video, INTRO_SECONDS)
        transcript = self.transcriber.transcribe(audio, LANGUAGE).strip()
        if transcript == "":
            return False
        result = self.jev.decide(
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
        return is_yes(result, "intro")
