from app.domain.judge import Judge
from app.domain.media import MediaSource
from app.domain.transcriber import Transcriber
from app.domain.youtube import YoutubeInspector
from app.usecase.rule import Rule
from app.usecase.rules.gen_visibility import GenVisibility
from app.usecase.rules.gen_youtube import GenYoutube
from app.usecase.rules.intro_required import IntroRequired
from app.usecase.rules.intro_same_take import IntroSameTake


def build_rules(
    inspector: YoutubeInspector,
    media: MediaSource,
    transcriber: Transcriber,
    jev: Judge,
) -> tuple[Rule, ...]:
    return (
        GenYoutube(),
        GenVisibility(inspector),
        IntroRequired(media, transcriber, jev),
        IntroSameTake(media),
    )
