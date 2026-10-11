from app.domain.clips import ReviewClips
from app.domain.judge import Judge, is_yes, noul
from app.domain.media import MediaSource
from app.domain.review import Review

INTRO_SECONDS = 2
ROUTINE_SECONDS = 60


class IntroSameTake:
    id = "INTRO-SAME-TAKE"

    def __init__(self, media: MediaSource) -> None:
        self.media = media

    def applies(self, review: Review) -> bool:
        return True

    def evaluate(self, review: Review, clips: ReviewClips | None, judge: Judge) -> bool:
        """0:02 と 1:00 のコマが同じ場所で撮られていれば True。"""
        if clips is not None:
            images = [clips.intro_frame, clips.routine_frame]
        else:
            images = [
                self.media.frame(review, INTRO_SECONDS),
                self.media.frame(review, ROUTINE_SECONDS),
            ]
        result = judge.decide(
            "Image 1 is the intro at 0:02 and image 2 is the routine at 1:00 "
            "of one beatbox video.",
            {
                "same_place": noul(
                    "Were both images recorded in the same place, "
                    "with the same background and setting?"
                )
            },
            images,
        )
        return is_yes(result, "same_place")
