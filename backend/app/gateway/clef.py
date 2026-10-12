import base64
import logging
import os

import httpx

logger = logging.getLogger(__name__)

account_env = "CLOUDFLARE_ACCOUNT_ID"
token_env = "CLOUDFLARE_API_TOKEN"
model_env = "CLEF_MODEL"
default_model = "clef-flash"


def data_url(image: bytes) -> str:
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif image.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        raise ValueError("image")
    encoded = base64.b64encode(image).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class ClefJudge:
    def decide(
        self,
        state: str | dict | list,
        questions: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        """Clef に state と questions を渡し、result を返す。"""
        account = os.environ.get(account_env, "").strip()
        token = os.environ.get(token_env, "").strip()
        if account == "" or token == "":
            raise RuntimeError("clef")
        model = os.environ.get(model_env, default_model).strip() or default_model
        body: dict = {"model": model, "state": state, "questions": questions}
        if images:
            if len(images) > 4:
                raise ValueError("images")
            body["images"] = [data_url(image) for image in images]
        url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}"
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json=body,
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("result", payload) if isinstance(payload, dict) else None
        if not isinstance(result, dict):
            raise RuntimeError("clef")
        logger.info(
            "clef model=%s questions=%s images=%d result=%s",
            model,
            list(questions),
            0 if images is None else len(images),
            result,
        )
        return result
