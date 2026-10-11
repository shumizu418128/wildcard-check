import unittest
from unittest.mock import MagicMock, patch

from app.domain.judge import Judge, is_yes
from app.domain.review import Review
from app.domain.youtube import YoutubeAccess
from app.gateway.clef import data_url
from app.gateway.yt_dlp_youtube import YtDlpYoutubeInspector
from app.usecase.gate_youtube import GateYoutube
from app.usecase.get_review import GetReview
from app.usecase.record_agreement import RecordAgreement
from app.usecase.rules.catalog import build_rules
from app.usecase.rules.gen_visibility import GenVisibility
from app.usecase.rules.no_short import NoShort
from app.usecase.rules.intro_required import IntroRequired
from app.usecase.rules.intro_same_take import IntroSameTake
from app.usecase.run_reviews import ReviewInput, RunReviews

PLAYABLE_FORMAT = {"vcodec": "avc1", "acodec": "mp4a"}


class FixedInspector:
    def __init__(self, access: YoutubeAccess = "public") -> None:
        self.access = access
        self.urls: list[str] = []

    def inspect(self, url: str) -> YoutubeAccess:
        self.urls.append(url)
        return self.access


def sample(category: str, source: str) -> Review:
    return Review(
        "job",
        category,
        source,
        "https://youtu.be/abcdefghijk",
        "https://example.com/raw",
        "running",
    )


class FakeMedia:
    def __init__(self) -> None:
        self.frames: list[float] = []
        self.audios: list[float] = []

    def frame(self, review: Review, video: bytes | None, seconds: float) -> bytes:
        self.frames.append(seconds)
        return f"frame-{seconds}".encode()

    def audio(self, review: Review, video: bytes | None, seconds: float) -> bytes:
        self.audios.append(seconds)
        return b"audio"


class FakeTranscriber:
    def __init__(self, text: str) -> None:
        self.text = text
        self.languages: list[str] = []

    def transcribe(self, audio: bytes, language: str) -> str:
        self.languages.append(language)
        return self.text


class NoulJudge:
    """質問ごとに決めた noul 値を、System One 形式で返す。"""

    def __init__(self, *values: float) -> None:
        self.values = list(values)
        self.calls: list[tuple[dict, list[bytes] | None]] = []

    def decide(
        self,
        state: str | dict | list,
        questions: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        self.calls.append((questions, images))
        value = self.values.pop(0)
        return {
            "model": "fake",
            "answers": {key: {"type": "noul", "noul": value} for key in questions},
        }


def default_rules():
    return build_rules(
        FixedInspector(), FakeMedia(), FakeTranscriber(""), UnusedJudge()
    )


def applicable_ids(category: str, source: str) -> list[str]:
    review = sample(category, source)
    return [rule.id for rule in default_rules() if rule.applies(review)]


class MemoryRepository:
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, bool]] = []
        self.done: list[str] = []
        self.reviews: dict[str, Review] = {}
        self.agreed: dict[str, list[str]] = {}

    def add(self, review: Review) -> None:
        self.reviews[review.id] = review

    def save_result(self, review_id: str, rule_id: str, ok: bool) -> None:
        self.saved.append((review_id, rule_id, ok))

    def mark_done(self, review_id: str) -> None:
        self.done.append(review_id)

    def get(self, review_id: str):
        review = self.reviews.get(review_id)
        if review is None:
            return None
        return review, []

    def save_agreement(self, review_id: str, rule_id: str) -> None:
        rows = self.agreed.setdefault(review_id, [])
        if rule_id not in rows:
            rows.append(rule_id)

    def agreements(self, review_id: str) -> list[str]:
        return list(self.agreed.get(review_id, []))


class UnusedJudge:
    def decide(
        self,
        state: str | dict | list,
        questions: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        raise AssertionError(state)


class ApplicableRuleTests(unittest.TestCase):
    def test_youtube_solo_includes_visibility(self):
        self.assertEqual(
            applicable_ids("solo", "youtube"),
            [
                "NO-SHORT",
                "GEN-VISIBILITY",
                "INTRO-REQUIRED",
                "INTRO-SAME-TAKE",
            ],
        )

    def test_file_crew_skips_youtube_rules(self):
        self.assertEqual(
            applicable_ids("crew", "file"),
            ["INTRO-REQUIRED", "INTRO-SAME-TAKE"],
        )


class AgreementTests(unittest.TestCase):
    def test_youtube_agreements_are_returned_in_order(self):
        repository = MemoryRepository()
        repository.add(sample("solo", "youtube"))
        record = RecordAgreement(repository)
        self.assertTrue(record.execute("job", "PLEDGE-A"))
        self.assertTrue(record.execute("job", "PLEDGE-B"))
        self.assertTrue(record.execute("job", "PLEDGE-A"))
        view = GetReview(repository, default_rules()).execute("job")
        assert view is not None
        self.assertEqual(view.agreements, ["PLEDGE-A", "PLEDGE-B"])

    def test_file_agreements_are_not_saved(self):
        repository = MemoryRepository()
        repository.add(sample("solo", "file"))
        self.assertFalse(RecordAgreement(repository).execute("job", "PLEDGE-A"))
        self.assertEqual(repository.agreements("job"), [])

    def test_missing_review_is_rejected(self):
        repository = MemoryRepository()
        self.assertFalse(RecordAgreement(repository).execute("job", "PLEDGE-A"))


class GenVisibilityTests(unittest.TestCase):
    def test_public_video_passes(self):
        inspector = FixedInspector("public")
        rule = GenVisibility(inspector)
        self.assertTrue(rule.evaluate(sample("solo", "youtube"), None, UnusedJudge()))
        self.assertEqual(inspector.urls, ["https://youtu.be/abcdefghijk"])

    def test_premiere_passes_visibility_rule(self):
        rule = GenVisibility(FixedInspector("premiere"))
        self.assertTrue(rule.evaluate(sample("solo", "youtube"), None, UnusedJudge()))

    def test_blocked_access_fails(self):
        for access in ("unlisted", "private", "unavailable", "unknown"):
            rule = GenVisibility(FixedInspector(access))
            self.assertFalse(
                rule.evaluate(sample("solo", "youtube"), None, UnusedJudge()), access
            )


class NoShortTests(unittest.TestCase):
    def evaluate(self, url: str, final_url: str) -> tuple[bool, MagicMock]:
        review = sample("solo", "youtube")
        review.youtube_url = url
        response = MagicMock()
        response.url = final_url
        with patch(
            "app.usecase.rules.no_short.requests.get", return_value=response
        ) as get:
            ok = NoShort().evaluate(review, None, UnusedJudge())
        return ok, get

    def test_normal_video_redirects_to_watch(self):
        ok, get = self.evaluate(
            "https://www.youtube.com/watch?v=abcdefghijk",
            "https://www.youtube.com/watch?v=abcdefghijk",
        )
        self.assertTrue(ok)
        self.assertEqual(
            get.call_args.args[0], "https://www.youtube.com/shorts/abcdefghijk"
        )

    def test_short_stays_on_shorts(self):
        ok, _ = self.evaluate(
            "https://youtu.be/abcdefghijk",
            "https://www.youtube.com/shorts/abcdefghijk",
        )
        self.assertFalse(ok)

    def test_non_video_url_fails(self):
        ok, get = self.evaluate("https://example.com/", "")
        self.assertFalse(ok)
        get.assert_not_called()


class IntroRequiredTests(unittest.TestCase):
    def test_greeting_passes(self):
        media = FakeMedia()
        transcriber = FakeTranscriber("My name is Taro, and this is my solo wildcard.")
        jev = NoulJudge(0.9)
        rule = IntroRequired(media, transcriber, jev)
        self.assertTrue(rule.evaluate(sample("solo", "file"), b"v", UnusedJudge()))
        self.assertEqual(media.audios, [30])
        self.assertEqual(transcriber.languages, ["en"])
        self.assertIsNone(jev.calls[0][1])

    def test_no_greeting_fails(self):
        rule = IntroRequired(FakeMedia(), FakeTranscriber("beatbox"), NoulJudge(0.1))
        self.assertFalse(rule.evaluate(sample("solo", "file"), b"v", UnusedJudge()))

    def test_silent_intro_skips_jev(self):
        rule = IntroRequired(FakeMedia(), FakeTranscriber("  "), UnusedJudge())
        self.assertFalse(rule.evaluate(sample("solo", "file"), b"v", UnusedJudge()))


class FrameRuleTests(unittest.TestCase):
    def test_same_take_sends_two_frames(self):
        media = FakeMedia()
        judge = NoulJudge(0.8)
        self.assertTrue(
            IntroSameTake(media).evaluate(sample("solo", "file"), b"v", judge)
        )
        self.assertEqual(media.frames, [2, 60])
        self.assertEqual(judge.calls[0][1], [b"frame-2", b"frame-60"])

    def test_same_take_fails_on_no(self):
        rule = IntroSameTake(FakeMedia())
        self.assertFalse(rule.evaluate(sample("solo", "file"), b"v", NoulJudge(0.2)))

    def test_threshold_is_inclusive(self):
        self.assertTrue(is_yes({"answers": {"a": {"type": "noul", "noul": 0.5}}}, "a"))


class GateYoutubeTests(unittest.TestCase):
    def test_returns_inspector_access(self):
        gate = GateYoutube(FixedInspector("premiere"))
        self.assertEqual(gate.execute("https://youtu.be/abcdefghijk"), "premiere")


class YtDlpYoutubeInspectorTests(unittest.TestCase):
    def test_upcoming_live_status_is_premiere(self):
        inspector = YtDlpYoutubeInspector()
        self.assertEqual(
            inspector._from_info({"live_status": "is_upcoming"}),
            "premiere",
        )

    def test_unlisted_availability(self):
        inspector = YtDlpYoutubeInspector()
        self.assertEqual(
            inspector._from_info({"availability": "unlisted"}),
            "unlisted",
        )

    def test_public_with_formats(self):
        inspector = YtDlpYoutubeInspector()
        info = {"availability": "public", "formats": [PLAYABLE_FORMAT]}
        self.assertEqual(inspector._from_info(info), "public")

    def test_public_without_downloadable_formats(self):
        inspector = YtDlpYoutubeInspector()
        storyboard = {"vcodec": "none", "acodec": "none"}
        drm = {"vcodec": "avc1", "acodec": "mp4a", "has_drm": True}
        for formats in ([], [storyboard], [drm]):
            info = {"availability": "public", "formats": formats}
            self.assertEqual(inspector._from_info(info), "unavailable", formats)

    def test_premiere_error_message(self):
        inspector = YtDlpYoutubeInspector()
        self.assertEqual(
            inspector._from_error("ERROR: [youtube] x: Premieres in 3 hours"),
            "premiere",
        )

    def test_extract_info_upcoming(self):
        inspector = YtDlpYoutubeInspector()
        fake_ydl = MagicMock()
        fake_ydl.__enter__.return_value = fake_ydl
        fake_ydl.__exit__.return_value = False
        fake_ydl.extract_info.return_value = {
            "live_status": "is_upcoming",
            "availability": "public",
        }
        with patch(
            "app.gateway.yt_dlp_youtube.yt_dlp.YoutubeDL", return_value=fake_ydl
        ):
            self.assertEqual(
                inspector.inspect("https://youtu.be/abcdefghijk"), "premiere"
            )

    def test_debug_fixture_urls(self):
        inspector = YtDlpYoutubeInspector()
        with patch.dict("os.environ", {"debug": "true"}):
            self.assertEqual(
                inspector.inspect("https://www.youtube.com/watch?v=SHORT-VIDEO"),
                "public",
            )
            self.assertEqual(
                inspector.inspect("https://www.youtube.com/watch?v=PREMIRE-VID"),
                "premiere",
            )
            self.assertEqual(
                inspector.inspect("https://www.youtube.com/watch?v=PRIVATE-VID"),
                "private",
            )

    def test_debug_fixture_off_calls_yt_dlp(self):
        inspector = YtDlpYoutubeInspector()
        fake_ydl = MagicMock()
        fake_ydl.__enter__.return_value = fake_ydl
        fake_ydl.__exit__.return_value = False
        fake_ydl.extract_info.return_value = {
            "availability": "public",
            "formats": [PLAYABLE_FORMAT],
        }
        with patch.dict("os.environ", {"debug": ""}, clear=False):
            with patch(
                "app.gateway.yt_dlp_youtube.yt_dlp.YoutubeDL", return_value=fake_ydl
            ):
                self.assertEqual(
                    inspector.inspect("https://www.youtube.com/watch?v=SHORT-VIDEO"),
                    "public",
                )
        fake_ydl.extract_info.assert_called_once()


class RunReviewsTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_bool_is_saved_before_done(self):
        repository = MemoryRepository()
        judge: Judge = UnusedJudge()

        class Answer:
            def __init__(self, rule_id: str, ok: bool, applies_to: bool = True) -> None:
                self.id = rule_id
                self.ok = ok
                self.applies_to = applies_to

            def applies(self, _review: Review) -> bool:
                return self.applies_to

            def evaluate(
                self, _review: Review, _video: bytes | None, _judge: Judge
            ) -> bool:
                return self.ok

        selected = (
            Answer("INTRO-REQUIRED", True),
            Answer("NO-SHORT", False, applies_to=False),
            Answer("INTRO-SAME-TAKE", False),
            Answer("GEN-VISIBILITY", True),
        )
        review_input = ReviewInput(sample("solo", "file"), b"keep")
        await RunReviews(repository, judge, selected).execute(review_input)
        self.assertEqual(
            repository.saved,
            [
                ("job", "INTRO-REQUIRED", True),
                ("job", "INTRO-SAME-TAKE", False),
                ("job", "GEN-VISIBILITY", True),
            ],
        )
        self.assertEqual(repository.done, ["job"])
        self.assertIsNone(review_input.video)

    async def test_debug_short_fixture_fails_no_short(self):
        repository = MemoryRepository()

        class Boom:
            def __init__(self, rule_id: str) -> None:
                self.id = rule_id

            def applies(self, _review: Review) -> bool:
                return True

            def evaluate(
                self, _review: Review, _video: bytes | None, _judge: Judge
            ) -> bool:
                raise AssertionError("evaluate")

        review = Review(
            "job",
            "solo",
            "youtube",
            "https://www.youtube.com/watch?v=SHORT-VIDEO",
            "https://example.com/raw",
            "running",
        )
        review_input = ReviewInput(review, None)
        selected = (Boom("NO-SHORT"), Boom("INTRO-REQUIRED"))
        with patch.dict("os.environ", {"debug": "true"}):
            await RunReviews(repository, UnusedJudge(), selected).execute(review_input)
        self.assertEqual(
            repository.saved,
            [
                ("job", "NO-SHORT", False),
                ("job", "INTRO-REQUIRED", True),
            ],
        )
        self.assertEqual(repository.done, ["job"])


class ClefImageTests(unittest.TestCase):
    def test_png_bytes_become_a_data_url(self):
        image = b"\x89PNG\r\n\x1a\nrest"
        self.assertTrue(data_url(image).startswith("data:image/png;base64,"))

    def test_unknown_bytes_are_rejected(self):
        with self.assertRaises(ValueError):
            data_url(b"not-an-image")


if __name__ == "__main__":
    unittest.main()
