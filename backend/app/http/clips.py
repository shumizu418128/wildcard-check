from fastapi import HTTPException, UploadFile

from app.domain.clips import ReviewClips

# 30 秒の 16kHz mono wav は約 1 MiB。切り出し結果だけを受ける。
MAX_AUDIO_BYTES = 4 * 1024 * 1024
MAX_FRAME_BYTES = 1024 * 1024


async def read_bounded(upload: UploadFile | None, limit: int, detail: str) -> bytes:
    """上限を超える分はメモリに載せない。"""
    if upload is None:
        raise HTTPException(status_code=400, detail=detail)
    data = await upload.read(limit + 1)
    if len(data) == 0 or len(data) > limit:
        raise HTTPException(status_code=400, detail=detail)
    return data


def require_wav(data: bytes, detail: str) -> bytes:
    if len(data) < 12 or not data.startswith(b"RIFF") or data[8:12] != b"WAVE":
        raise HTTPException(status_code=400, detail=detail)
    return data


def require_jpeg(data: bytes, detail: str) -> bytes:
    if not data.startswith(b"\xff\xd8"):
        raise HTTPException(status_code=400, detail=detail)
    return data


async def read_review_clips(
    intro_audio: UploadFile | None,
    intro_frame: UploadFile | None,
    routine_frame: UploadFile | None,
) -> ReviewClips:
    audio = require_wav(
        await read_bounded(intro_audio, MAX_AUDIO_BYTES, "intro_audio"),
        "intro_audio",
    )
    intro = require_jpeg(
        await read_bounded(intro_frame, MAX_FRAME_BYTES, "intro_frame"),
        "intro_frame",
    )
    routine = require_jpeg(
        await read_bounded(routine_frame, MAX_FRAME_BYTES, "routine_frame"),
        "routine_frame",
    )
    return ReviewClips(audio, intro, routine)
