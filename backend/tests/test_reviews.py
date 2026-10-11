import socket
import unittest
from unittest.mock import MagicMock, patch

import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.domain.judge import Judge, is_yes
from app.domain.review import Review
from app.domain.youtube import YoutubeAccess
from app.gateway.clef import data_url
from app.gateway.yt_dlp_youtube import YtDlpYoutubeInspector
from app.http.controller import register
from app.http.origin import header, require_origin
from app.usecase.create_review import CreateReview
from app.usecase.gate_youtube import GateYoutube
from app.usecase.get_review import GetReview
from app.usecase.record_agreement import RecordAgreement
from app.usecase.rules.catalog import build_rules
from app.usecase.rules.gen_visibility import GenVisibility
from app.usecase.rules.no_short import NoShort
from app.usecase.rules.sub_raw import SubRaw
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
    return build_rules(FixedInspector(), FakeMedia(), FakeTranscriber(""))


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
                "SUB-RAW",
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


class SubRawTests(unittest.TestCase):
    def response(self, status: int, content_type: str = "text/html") -> MagicMock:
        response = MagicMock()
        response.status_code = status
        response.headers = {"Content-Type": content_type}
        response.iter_content.return_value = iter(())
        return response

    def evaluate(self, response: MagicMock) -> bool:
        review = sample("solo", "youtube")
        with (
            patch("app.usecase.rules.sub_raw._is_safe_url", return_value=True),
            patch("app.usecase.rules.sub_raw.requests.get", side_effect=[response]),
        ):
            return SubRaw().evaluate(review, None, UnusedJudge())

    def test_missing_link_fails(self):
        missing = self.response(404)
        self.assertFalse(self.evaluate(missing))
        missing.iter_content.assert_not_called()

    def test_gone_and_unauthorized_fail(self):
        self.assertFalse(self.evaluate(self.response(401)))
        self.assertFalse(self.evaluate(self.response(410)))

    def test_forbidden_and_server_error_pass(self):
        blocked = self.response(403)
        blocked.iter_content.return_value = iter([b"You need access"])
        self.assertTrue(self.evaluate(blocked))
        blocked.iter_content.assert_not_called()
        self.assertTrue(self.evaluate(self.response(500)))

    def test_timeout_passes(self):
        review = sample("solo", "youtube")
        with (
            patch("app.usecase.rules.sub_raw._is_safe_url", return_value=True),
            patch(
                "app.usecase.rules.sub_raw.requests.get",
                side_effect=requests.Timeout("slow"),
            ),
        ):
            ok = SubRaw().evaluate(review, None, UnusedJudge())
        self.assertTrue(ok)

    def test_login_host_fails_without_a_second_request(self):
        review = sample("solo", "youtube")
        redirected = self.response(302)
        redirected.headers["Location"] = "https://accounts.google.com/ServiceLogin"
        with (
            patch("app.usecase.rules.sub_raw._is_safe_url", return_value=True),
            patch(
                "app.usecase.rules.sub_raw.requests.get", return_value=redirected
            ) as get,
        ):
            ok = SubRaw().evaluate(review, None, UnusedJudge())
        self.assertFalse(ok)
        self.assertEqual(get.call_count, 1)

    def test_access_wall_fails_and_sign_in_chrome_passes(self):
        wall = self.response(200)
        wall.iter_content.return_value = iter([b"<html>You need access</html>"])
        self.assertFalse(self.evaluate(wall))
        chrome = self.response(200)
        chrome.iter_content.return_value = iter([b"<a>Sign in</a>"])
        self.assertTrue(self.evaluate(chrome))

    def test_file_response_is_not_read(self):
        media = self.response(200, "audio/wav")
        self.assertTrue(self.evaluate(media))
        media.iter_content.assert_not_called()

    def test_private_address_is_not_requested(self):
        review = sample("solo", "youtube")
        dns = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]
        with (
            patch("app.usecase.rules.sub_raw.socket.getaddrinfo", return_value=dns),
            patch("app.usecase.rules.sub_raw.requests.get") as get,
        ):
            ok = SubRaw().evaluate(review, None, UnusedJudge())
        self.assertTrue(ok)
        get.assert_not_called()

    def test_blank_raw_url_does_not_apply(self):
        review = sample("solo", "youtube")
        review.raw_url = "  "
        self.assertFalse(SubRaw().applies(review))


class IntroRequiredTests(unittest.TestCase):
    def test_greeting_passes(self):
        media = FakeMedia()
        transcriber = FakeTranscriber("My name is Taro, and this is my solo wildcard.")
        judge = NoulJudge(0.9)
        rule = IntroRequired(media, transcriber)
        self.assertTrue(rule.evaluate(sample("solo", "file"), b"v", judge))
        self.assertEqual(media.audios, [30])
        self.assertEqual(transcriber.languages, ["en"])
        self.assertIsNone(judge.calls[0][1])

    def test_no_greeting_fails(self):
        rule = IntroRequired(FakeMedia(), FakeTranscriber("beatbox"))
        self.assertFalse(rule.evaluate(sample("solo", "file"), b"v", NoulJudge(0.1)))

    def test_silent_intro_skips_judge(self):
        rule = IntroRequired(FakeMedia(), FakeTranscriber("  "))
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
        with (
            patch.dict("os.environ", {"debug": "true"}),
            patch(
                "app.gateway.yt_dlp_youtube.debug_gate_delay", return_value=0
            ) as delay,
        ):
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
        self.assertEqual(delay.call_count, 3)

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
        with (
            patch.dict("os.environ", {"debug": "true"}),
            patch(
                "app.usecase.run_reviews.debug_rule_delay", return_value=0
            ) as delay,
        ):
            await RunReviews(repository, UnusedJudge(), selected).execute(review_input)
        self.assertEqual(delay.call_count, 2)
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


class NoopRun:
    def execute(self, data: ReviewInput) -> None:
        pass


def build_api(secret: str = "") -> FastAPI:
    app = FastAPI()
    register(app, require_origin(secret))
    repository = MemoryRepository()
    app.state.create_review = CreateReview(repository)
    app.state.get_review = GetReview(repository, ())
    app.state.run_reviews = NoopRun()
    return app


def post_file(client: TestClient, source: str = "file"):
    return client.post(
        "/api/reviews",
        data={"category": "solo", "source": source},
        files={"file": ("clip.mp4", b"video", "video/mp4")},
    )


class OriginGuardTests(unittest.TestCase):
    def test_missing_header_is_rejected(self):
        client = TestClient(build_api("secret"))
        self.assertEqual(client.get("/api/reviews/none").status_code, 403)

    def test_wrong_header_is_rejected(self):
        client = TestClient(build_api("secret"))
        response = client.get("/api/reviews/none", headers={header: "nope"})
        self.assertEqual(response.status_code, 403)

    def test_matching_header_passes(self):
        client = TestClient(build_api("secret"))
        response = client.get("/api/reviews/none", headers={header: "secret"})
        self.assertEqual(response.status_code, 404)

    def test_health_is_open(self):
        client = TestClient(build_api("secret"))
        self.assertEqual(client.get("/api/health").status_code, 200)

    def test_empty_secret_disables_guard(self):
        client = TestClient(build_api(""))
        self.assertEqual(client.get("/api/reviews/none").status_code, 404)


if __name__ == "__main__":
    unittest.main()
