from typing import Protocol

# Clef / Jev に既定の閾値はない。noul の確率がこれ以上なら yes とみなす
YES_THRESHOLD = 0.5


class Judge(Protocol):
    def decide(
        self,
        state: str | dict | list,
        questions: dict,
        images: list[bytes] | None = None,
    ) -> dict: ...


def noul(instructions: str) -> dict:
    return {"type": "noul", "instructions": instructions}


def is_yes(result: dict, key: str) -> bool:
    """System One 形式の result から noul 回答を読み、yes か返す。"""
    answer = result["answers"][key]
    return float(answer["noul"]) >= YES_THRESHOLD
