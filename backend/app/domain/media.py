from typing import Protocol

from app.domain.review import Review


class MediaSource(Protocol):
    def frame(self, review: Review, seconds: float) -> bytes:
        """指定秒のコマを JPEG で返す。YouTube の配信から切り出す。"""
        ...

    def audio(self, review: Review, seconds: float) -> bytes:
        """冒頭から指定秒までの音声を 16kHz mono wav で返す。"""
        ...
