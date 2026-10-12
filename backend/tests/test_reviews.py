import socket
import unittest
from unittest.mock import MagicMock, patch

import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from limits import parse
from app.domain.clips import ReviewClips
from app.domain.judge import Judge, is_yes
from app.domain.review import Review
from app.domain.youtube import YoutubeAccess
from app.gateway.clef import data_url
from app.gateway.youtube_data_api import YoutubeDataApiInspector
from app.http.clips import MAX_AUDIO_BYTES
from app.http.controller import register
from app.http.origin import header, require_origin
from app.http.rate_limit import limit_reviews
from app.usecase.create_review import CreateReview
from app.usecase.gate_youtube import GateYoutube
from app.usecase.get_review import GetReview
from app.usecase.record_agreement import RecordAgreement
from app.usecase.rules.catalog import build_rules
from app.usecase.rules.gen_visibility import GenVisibility
from app.usecase.rules.intro_required import IntroRequired
from app.usecase.rules.intro_same_take import IntroSameTake
from app.usecase.rules.sub_raw import SubRaw
from app.usecase.run_reviews import ReviewInput, RunReviews

CLIPS = ReviewClips(b"RIFF\x00\x00\x00\x00WAVEaudio", b"\xff\xd8i", b"\xff\xd8r")


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


class FakeTranscriber:
    def __init__(self, text: str) -> None:
        self.text = text
        self.languages: list[str] = []
        self.audios: list[bytes] = []

    def transcribe(self, audio: bytes, language: str) -> str:
        self.languages.append(language)
        self.audios.append(audio)
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
    return build_rules(FixedInspector(), FakeTranscriber(""))


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
        self.assertTrue(rule.evaluate(sample("solo", "youtube"), CLIPS, UnusedJudge()))
        self.assertEqual(inspector.urls, ["https://youtu.be/abcdefghijk"])

    def test_blocked_access_fails(self):
        for access in ("unlisted", "private", "unknown"):
            rule = GenVisibility(FixedInspector(access))
            self.assertFalse(
                rule.evaluate(sample("solo", "youtube"), CLIPS, UnusedJudge()), access
            )


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
            return SubRaw().evaluate(review, CLIPS, UnusedJudge())

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
            ok = SubRaw().evaluate(review, CLIPS, UnusedJudge())
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
            ok = SubRaw().evaluate(review, CLIPS, UnusedJudge())
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
            ok = SubRaw().evaluate(review, CLIPS, UnusedJudge())
        self.assertTrue(ok)
        get.assert_not_called()

    def test_blank_raw_url_does_not_apply(self):
        review = sample("solo", "youtube")
        review.raw_url = "  "
        self.assertFalse(SubRaw().applies(review))


class IntroRequiredTests(unittest.TestCase):
    def test_greeting_passes(self):
        transcriber = FakeTranscriber("My name is Taro, and this is my solo wildcard.")
        judge = NoulJudge(0.9)
        rule = IntroRequired(transcriber)
        self.assertTrue(rule.evaluate(sample("solo", "youtube"), CLIPS, judge))
        self.assertEqual(transcriber.audios, [CLIPS.intro_audio])
        self.assertEqual(transcriber.languages, ["en"])
        self.assertIsNone(judge.calls[0][1])

    def test_no_greeting_fails(self):
        rule = IntroRequired(FakeTranscriber("beatbox"))
        self.assertFalse(rule.evaluate(sample("solo", "youtube"), CLIPS, NoulJudge(0.1)))

    def test_silent_intro_skips_judge(self):
        rule = IntroRequired(FakeTranscriber("  "))
        self.assertFalse(rule.evaluate(sample("solo", "youtube"), CLIPS, UnusedJudge()))


class FrameRuleTests(unittest.TestCase):
    def test_same_take_uses_uploaded_frames(self):
        judge = NoulJudge(0.8)
        clips = ReviewClips(b"audio", b"intro", b"routine")
        self.assertTrue(IntroSameTake().evaluate(sample("solo", "youtube"), clips, judge))
        self.assertEqual(judge.calls[0][1], [b"intro", b"routine"])

    def test_same_take_fails_on_no(self):
        rule = IntroSameTake()
        self.assertFalse(rule.evaluate(sample("solo", "file"), CLIPS, NoulJudge(0.2)))

    def test_threshold_is_inclusive(self):
        self.assertTrue(is_yes({"answers": {"a": {"type": "noul", "noul": 0.5}}}, "a"))


class GateYoutubeTests(unittest.TestCase):
    def test_returns_inspector_access(self):
        gate = GateYoutube(FixedInspector("unlisted"))
        self.assertEqual(gate.execute("https://youtu.be/abcdefghijk"), "unlisted")


class YoutubeDataApiInspectorTests(unittest.TestCase):
    def response(self, payload: object, ok: bool = True) -> MagicMock:
        response = MagicMock()
        response.ok = ok
        response.json.return_value = payload
        return response

    def inspect(self, response: MagicMock, key: str = "key") -> YoutubeAccess:
        with (
            patch.dict("os.environ", {"debug": "", "YOUTUBE_API_KEY": key}),
            patch(
                "app.gateway.youtube_data_api.requests.get", return_value=response
            ) as get,
        ):
            access = YoutubeDataApiInspector().inspect("https://youtu.be/abcdefghijk")
        self.last_get = get
        return access

    def test_privacy_status_is_returned(self):
        for privacy in ("public", "unlisted", "private"):
            payload = {"items": [{"status": {"privacyStatus": privacy}}]}
            self.assertEqual(self.inspect(self.response(payload)), privacy)
        params = self.last_get.call_args.kwargs["params"]
        self.assertEqual(params["id"], "abcdefghijk")
        self.assertEqual(params["part"], "status")

    def test_missing_video_is_private(self):
        self.assertEqual(self.inspect(self.response({"items": []})), "private")

    def test_api_error_is_unknown(self):
        self.assertEqual(self.inspect(self.response({}, ok=False)), "unknown")
        self.assertEqual(self.inspect(self.response({"items": [{}]})), "unknown")

    def test_missing_key_skips_request(self):
        self.assertEqual(self.inspect(self.response({}), key=""), "unknown")
        self.last_get.assert_not_called()

    def test_network_error_is_unknown(self):
        with (
            patch.dict("os.environ", {"debug": "", "YOUTUBE_API_KEY": "key"}),
            patch(
                "app.gateway.youtube_data_api.requests.get",
                side_effect=requests.Timeout("slow"),
            ),
        ):
            access = YoutubeDataApiInspector().inspect("https://youtu.be/abcdefghijk")
        self.assertEqual(access, "unknown")

    def test_debug_fixture_urls(self):
        inspector = YoutubeDataApiInspector()
        with (
            patch.dict("os.environ", {"debug": "true"}),
            patch(
                "app.gateway.youtube_data_api.debug_gate_delay", return_value=0
            ) as delay,
            patch("app.gateway.youtube_data_api.requests.get") as get,
        ):
            self.assertEqual(
                inspector.inspect("https://www.youtube.com/watch?v=SHORT-VIDEO"),
                "public",
            )
            self.assertEqual(
                inspector.inspect("https://www.youtube.com/watch?v=PRIVATE-VID"),
                "private",
            )
        self.assertEqual(delay.call_count, 2)
        get.assert_not_called()


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
                self, _review: Review, _clips: ReviewClips | None, _judge: Judge
            ) -> bool:
                return self.ok

        selected = (
            Answer("INTRO-REQUIRED", True),
            Answer("NO-SHORT", False, applies_to=False),
            Answer("INTRO-SAME-TAKE", False),
            Answer("GEN-VISIBILITY", True),
        )
        review_input = ReviewInput(
            sample("solo", "file"),
            ReviewClips(b"keep", b"intro", b"routine"),
        )
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
        self.assertIsNone(review_input.clips)

    async def test_debug_fixture_passes_every_rule(self):
        repository = MemoryRepository()

        class Boom:
            def __init__(self, rule_id: str) -> None:
                self.id = rule_id

            def applies(self, _review: Review) -> bool:
                return True

            def evaluate(
                self, _review: Review, _clips: ReviewClips | None, _judge: Judge
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
        review_input = ReviewInput(review)
        selected = (Boom("SUB-RAW"), Boom("INTRO-REQUIRED"))
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
                ("job", "SUB-RAW", True),
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
    limit_reviews(app, parse("1 per 10 seconds"))
    register(app, require_origin(secret))
    repository = MemoryRepository()
    app.state.create_review = CreateReview(repository)
    app.state.get_review = GetReview(repository, ())
    app.state.run_reviews = NoopRun()
    return app


def wav_bytes() -> bytes:
    return b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"rest"


def jpeg_bytes() -> bytes:
    return b"\xff\xd8" + b"jpeg"


def post_file(client: TestClient, source: str = "file"):
    return client.post(
        "/api/reviews",
        data={"category": "solo", "source": source},
        files={
            "intro_audio": ("intro.wav", wav_bytes(), "audio/wav"),
            "intro_frame": ("intro.jpg", jpeg_bytes(), "image/jpeg"),
            "routine_frame": ("routine.jpg", jpeg_bytes(), "image/jpeg"),
        },
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


class ClipUploadTests(unittest.TestCase):
    def test_file_without_clips_is_rejected(self):
        client = TestClient(build_api())
        response = client.post(
            "/api/reviews", data={"category": "solo", "source": "file"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "intro_audio")

    def test_oversized_audio_is_rejected(self):
        client = TestClient(build_api())
        audio = b"RIFF" + (b"\x00" * 4) + b"WAVE" + (b"x" * MAX_AUDIO_BYTES)
        response = client.post(
            "/api/reviews",
            data={"category": "solo", "source": "file"},
            files={
                "intro_audio": ("intro.wav", audio, "audio/wav"),
                "intro_frame": ("intro.jpg", jpeg_bytes(), "image/jpeg"),
                "routine_frame": ("routine.jpg", jpeg_bytes(), "image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "intro_audio")

    def test_non_jpeg_frame_is_rejected(self):
        client = TestClient(build_api())
        response = client.post(
            "/api/reviews",
            data={"category": "solo", "source": "file"},
            files={
                "intro_audio": ("intro.wav", wav_bytes(), "audio/wav"),
                "intro_frame": ("intro.jpg", b"not-jpeg", "image/jpeg"),
                "routine_frame": ("routine.jpg", jpeg_bytes(), "image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "intro_frame")

    def test_youtube_without_clips_is_rejected(self):
        app = build_api()
        inspector = FixedInspector("public")
        app.state.gate_youtube = GateYoutube(inspector)
        client = TestClient(app)
        response = client.post(
            "/api/reviews",
            data={
                "category": "solo",
                "source": "youtube",
                "youtube_url": "https://youtu.be/abcdefghijk",
                "raw_url": "https://example.com/raw",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "intro_audio")
        self.assertEqual(inspector.urls, [])

    def test_unlisted_youtube_is_rejected(self):
        app = build_api()
        app.state.gate_youtube = GateYoutube(FixedInspector("unlisted"))
        client = TestClient(app)
        response = client.post(
            "/api/reviews",
            data={
                "category": "solo",
                "source": "youtube",
                "youtube_url": "https://youtu.be/abcdefghijk",
                "raw_url": "https://example.com/raw",
            },
            files={
                "intro_audio": ("intro.wav", wav_bytes(), "audio/wav"),
                "intro_frame": ("intro.jpg", jpeg_bytes(), "image/jpeg"),
                "routine_frame": ("routine.jpg", jpeg_bytes(), "image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "unlisted_url")

    def test_file_post_keeps_clips(self):
        app = build_api()

        class CaptureRun:
            def __init__(self) -> None:
                self.seen: ReviewInput | None = None

            def execute(self, data: ReviewInput) -> None:
                self.seen = data

        run = CaptureRun()
        app.state.run_reviews = run
        client = TestClient(app)
        self.assertEqual(post_file(client).status_code, 201)
        self.assertIsNotNone(run.seen)
        assert run.seen is not None and run.seen.clips is not None
        self.assertTrue(run.seen.clips.intro_audio.startswith(b"RIFF"))
        self.assertTrue(run.seen.clips.intro_frame.startswith(b"\xff\xd8"))
        self.assertTrue(run.seen.clips.routine_frame.startswith(b"\xff\xd8"))


class RateLimitTests(unittest.TestCase):
    def test_second_review_within_window_is_rejected(self):
        client = TestClient(build_api())
        self.assertEqual(post_file(client).status_code, 201)
        response = post_file(client)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json(), {"detail": "rate_limited"})
        self.assertIn("retry-after", response.headers)

    def test_failed_review_is_not_counted(self):
        client = TestClient(build_api())
        self.assertEqual(post_file(client, source="bad").status_code, 400)
        self.assertEqual(post_file(client).status_code, 201)

    def test_other_ip_is_counted_separately(self):
        app = build_api()
        first = TestClient(app, client=("192.0.2.1", 50000))
        second = TestClient(app, client=("192.0.2.2", 50000))
        self.assertEqual(post_file(first).status_code, 201)
        self.assertEqual(post_file(second).status_code, 201)

    def test_polling_is_not_limited(self):
        client = TestClient(build_api())
        for _ in range(3):
            self.assertEqual(client.get("/api/reviews/none").status_code, 404)


if __name__ == "__main__":
    unittest.main()
