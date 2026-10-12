from app.domain.transcriber import Transcriber
from app.domain.youtube import YoutubeInspector
from app.usecase.rule import Rule
from app.usecase.rules.gen_visibility import GenVisibility
from app.usecase.rules.intro_required import IntroRequired
from app.usecase.rules.intro_same_take import IntroSameTake
from app.usecase.rules.no_short import NoShort
from app.usecase.rules.sub_raw import SubRaw


def build_rules(
    inspector: YoutubeInspector,
    transcriber: Transcriber,
) -> tuple[Rule, ...]:
    return (
        NoShort(),
        SubRaw(),
        GenVisibility(inspector),
        IntroRequired(transcriber),
        IntroSameTake(),
    )
