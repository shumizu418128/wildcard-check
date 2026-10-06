from typing import Protocol


class Transcriber(Protocol):
    def transcribe(self, audio: bytes, language: str) -> str: ...
