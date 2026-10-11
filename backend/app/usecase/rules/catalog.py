from app.domain.judge import Judge
from app.domain.media import MediaSource
from app.domain.transcriber import Transcriber
from app.domain.youtube import YoutubeInspector
from app.usecase.rule import Rule
from app.usecase.rules.gen_visibility import GenVisibility
from app.usecase.rules.intro_required import IntroRequired
from app.usecase.rules.intro_same_take import IntroSameTake
from app.usecase.rules.no_short import NoShort


def build_rules(
    inspector: YoutubeInspector,
    media: MediaSource,
    transcriber: Transcriber,
    jev: Judge,
) -> tuple[Rule, ...]:
    return (
        NoShort(),
        GenVisibility(inspector),
        IntroRequired(media, transcriber, jev),
        IntroSameTake(media),
    )
