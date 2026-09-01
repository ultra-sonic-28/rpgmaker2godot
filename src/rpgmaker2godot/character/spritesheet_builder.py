"""AnalysisResult → internal character model transformation."""

from rpgmaker2godot.analysis.models import (
    CharacterAnalysisResult,
    CharacterSheetInfo,
)

from .layout import CHARACTER_ANIMATIONS, CharacterAnimationSpec
from .models import (
    CharacterAnimation,
    CharacterConversionResult,
    CharacterFrame,
    CharacterSpriteSheet,
)


class CharacterSpriteSheetBuilder:
    """Build the internal character representation from an analysis.

    Every ``CharacterSheetInfo`` is turned into a
    :class:`~rpgmaker2godot.character.models.CharacterSpriteSheet`
    holding one :class:`~rpgmaker2godot.character.models.CharacterAnimation`
    per row of the fixed layout, each with its frame regions.

    Two-frame animations (the idle rows) simply emit their first two
    cells — the third cell of those rows is expected to be empty in
    the source image and is never referenced.

    Playback settings (speed, duration, loop) can be overridden per
    animation name through ``animation_overrides`` — a mapping of
    ``name -> (speed, duration, loop)`` used to tune the animations
    from the ``rpgmaker2godot.yaml`` configuration file.
    """

    def __init__(
        self,
        animation_overrides: dict[str, tuple[float, float, bool]] | None = None,
    ) -> None:
        self._animation_overrides = animation_overrides or {}

    def convert(
        self,
        analysis: CharacterAnalysisResult,
    ) -> CharacterConversionResult:
        return CharacterConversionResult(
            sheets=tuple(
                self._convert_sheet(sheet_info)
                for sheet_info in analysis.sheets
            )
        )

    def _convert_sheet(
        self,
        sheet_info: CharacterSheetInfo,
    ) -> CharacterSpriteSheet:
        return CharacterSpriteSheet(
            name=sheet_info.path.stem,
            source_path=sheet_info.path,
            width=sheet_info.width,
            height=sheet_info.height,
            frame_width=sheet_info.frame_width,
            frame_height=sheet_info.frame_height,
            animations=tuple(
                self._build_animation(
                    spec,
                    sheet_info,
                    self._animation_overrides.get(spec.name),
                )
                for spec in CHARACTER_ANIMATIONS
            ),
        )

    @staticmethod
    def _build_animation(
        spec: CharacterAnimationSpec,
        sheet_info: CharacterSheetInfo,
        override: tuple[float, float, bool] | None,
    ) -> CharacterAnimation:
        if override is not None:
            speed, duration, loop = override
        else:
            speed = spec.speed
            duration = spec.duration
            loop = spec.loop

        frames = tuple(
            CharacterFrame(
                column=column,
                row=spec.row,
                x=column * sheet_info.frame_width,
                y=spec.row * sheet_info.frame_height,
                width=sheet_info.frame_width,
                height=sheet_info.frame_height,
            )
            for column in range(spec.frame_count)
        )

        return CharacterAnimation(
            name=spec.name,
            speed=speed,
            duration=duration,
            loop=loop,
            frames=frames,
        )
