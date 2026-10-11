import os
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import TYPE_CHECKING, Any, cast

import imageio_ffmpeg
import yt_dlp

from app.domain.review import Review

if TYPE_CHECKING:
    from yt_dlp import _Params

FRAME_FORMAT = "bv*[height<=720]/b"
AUDIO_FORMAT = "ba/b"
# Clef の画像上限 (4 MiB / 16 MP) に収める
FRAME_FILTER = "scale='min(1280,iw)':-2"


@lru_cache(maxsize=16)
def stream(url: str, selector: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    """yt-dlp で直接再生できる URL と、そのとき必要な HTTP ヘッダーを返す。"""
    # typeshed の skip_download は str なので、bool を渡すために cast する
    ydl_opts: _Params = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": cast(Any, True),
        "format": selector,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not isinstance(info, dict) or not isinstance(info.get("url"), str):
        raise RuntimeError("stream")
    headers = info.get("http_headers") or {}
    return info["url"], tuple((str(k), str(v)) for k, v in headers.items())


def header_args(headers: tuple[tuple[str, str], ...]) -> list[str]:
    if not headers:
        return []
    return ["-headers", "".join(f"{key}: {value}\r\n" for key, value in headers)]


def run(args: list[str]) -> bytes:
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error"]
    done = subprocess.run(command + args, capture_output=True, check=False, timeout=300)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.decode("utf-8", "replace").strip() or "ffmpeg")
    return done.stdout


@contextmanager
def temp_path(suffix: str, data: bytes | None = None) -> Iterator[str]:
    handle, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(handle, "wb") as file:
            if data is not None:
                file.write(data)
        yield path
    finally:
        os.remove(path)


class FfmpegMedia:
    def frame(self, review: Review, seconds: float) -> bytes:
        with self._input(review, FRAME_FORMAT) as (source, headers):
            image = run(
                [
                    *headers,
                    "-ss",
                    str(seconds),
                    "-i",
                    source,
                    "-frames:v",
                    "1",
                    "-vf",
                    FRAME_FILTER,
                    "-f",
                    "image2",
                    "-c:v",
                    "mjpeg",
                    "pipe:1",
                ]
            )
        if image == b"":
            raise RuntimeError("frame")
        return image

    def audio(self, review: Review, seconds: float) -> bytes:
        with (
            self._input(review, AUDIO_FORMAT) as (source, headers),
            temp_path(".wav") as output,
        ):
            # wav をパイプに書くとヘッダーのサイズが埋まらないので、ファイルに書く
            run(
                [
                    *headers,
                    "-i",
                    source,
                    "-t",
                    str(seconds),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-y",
                    output,
                ]
            )
            with open(output, "rb") as file:
                return file.read()

    @contextmanager
    def _input(self, review: Review, selector: str) -> Iterator[tuple[str, list[str]]]:
        if review.youtube_url == "":
            raise RuntimeError("video")
        url, headers = stream(review.youtube_url, selector)
        yield url, header_args(headers)
