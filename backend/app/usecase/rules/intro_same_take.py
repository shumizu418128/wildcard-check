from app.domain.clips import ReviewClips
from app.domain.judge import Judge, is_yes, noul
from app.domain.review import Review


class IntroSameTake:
    id = "INTRO-SAME-TAKE"

    def applies(self, review: Review) -> bool:
        return True

    def evaluate(self, review: Review, clips: ReviewClips, judge: Judge) -> bool:
        """0:02 と 1:00 のコマが同じ場所で撮られていれば True。"""
        result = judge.decide(
            "Image 1 is the intro at 0:02 and image 2 is the routine at 1:00 "
            "of one beatbox video.",
            {
                "same_place": noul(
                    "Were both images recorded in the same place, "
                    "with the same background and setting?"
                )
            },
            [clips.intro_frame, clips.routine_frame],
        )
        return is_yes(result, "same_place")
