from dataclasses import dataclass


@dataclass
class ReviewClips:
    """ブラウザが切り出した審査用の成果物。動画本体は含まない。"""

    intro_audio: bytes
    intro_frame: bytes
    routine_frame: bytes
