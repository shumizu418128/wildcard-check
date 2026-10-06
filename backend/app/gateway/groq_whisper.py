import os

import httpx

key_env = "GROQ_API_KEY"
model_env = "GROQ_WHISPER_MODEL"
default_model = "whisper-large-v3-turbo"
url = "https://api.groq.com/openai/v1/audio/transcriptions"


class GroqWhisper:
    def transcribe(self, audio: bytes, language: str) -> str:
        """Groq の Whisper API に wav を送り、本文を返す。"""
        key = os.environ.get(key_env, "").strip()
        if key == "":
            raise RuntimeError("groq")
        model = os.environ.get(model_env, default_model).strip() or default_model
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            data={"model": model, "language": language, "response_format": "json"},
            files={"file": ("audio.wav", audio, "audio/wav")},
            timeout=120,
        )
        response.raise_for_status()
        text = response.json().get("text")
        if not isinstance(text, str):
            raise RuntimeError("groq")
        return text
