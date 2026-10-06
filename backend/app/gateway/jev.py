import os

import httpx

key_env = "TYPESAFE_API_KEY"
model_env = "JEV_MODEL"
url_env = "JEV_URL"
default_model = "jev-latest"
default_url = "https://api.typesafe.ai/v1/systemone"


class JevJudge:
    def decide(
        self,
        state: str | dict | list,
        questions: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        """Jev に state と questions を渡し、{model, answers, usage} を返す。"""
        if images:
            raise ValueError("images")
        key = os.environ.get(key_env, "").strip()
        if key == "":
            raise RuntimeError("jev")
        model = os.environ.get(model_env, default_model).strip() or default_model
        endpoint = os.environ.get(url_env, default_url).strip() or default_url
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "state": state, "questions": questions},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("jev")
        return payload
