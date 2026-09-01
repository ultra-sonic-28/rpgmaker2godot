from pathlib import Path

from rpgmaker2godot.analysis.models import (
    CharacterAnalysisResult,
    CharacterSheetInfo,
)
from rpgmaker2godot.character.layout import (
    CHARACTER_ANIMATIONS,
    DAMAGED_FPS,
    IDLE_FPS,
    WALK_FPS,
)
from rpgmaker2godot.character.spritesheet_builder import (
    CharacterSpriteSheetBuilder,
)


def build_analysis() -> CharacterAnalysisResult:
    sheet_info = CharacterSheetInfo(
        path=Path("characters/player-1.png"),
        width=144,
        height=432,
        frame_width=48,
        frame_height=48,
        columns=3,
        rows=9,
    )

    return CharacterAnalysisResult(
        input_directory=Path("characters"),
        sheets=(sheet_info,),
        warnings=(),
    )


def test_converts_every_layout_animation() -> None:
    conversion = CharacterSpriteSheetBuilder().convert(build_analysis())

    assert len(conversion.sheets) == 1

    sheet = conversion.sheets[0]

    assert sheet.name == "player-1"
    assert (sheet.width, sheet.height) == (144, 432)
    assert (sheet.frame_width, sheet.frame_height) == (48, 48)

    assert [animation.name for animation in sheet.animations] == [
        "walk-down",
        "walk-left",
        "walk-right",
        "walk-up",
        "idle-down",
        "idle-left",
        "idle-right",
        "idle-up",
        "damaged",
    ]

    assert sheet.frame_count == 23


def test_frame_counts_follow_the_layout() -> None:
    conversion = CharacterSpriteSheetBuilder().convert(build_analysis())

    sheet = conversion.sheets[0]

    counts = [
        len(animation.frames)
        for animation in sheet.animations
    ]

    assert counts == [3, 3, 3, 3, 2, 2, 2, 2, 3]


def test_frame_regions_match_the_layout_rows() -> None:
    conversion = CharacterSpriteSheetBuilder().convert(build_analysis())

    sheet = conversion.sheets[0]

    walk_left = sheet.animations[1]

    assert [frame.column for frame in walk_left.frames] == [0, 1, 2]
    assert [frame.row for frame in walk_left.frames] == [1, 1, 1]
    assert [(frame.x, frame.y) for frame in walk_left.frames] == [
        (0, 48),
        (48, 48),
        (96, 48),
    ]
    assert all(
        frame.width == 48 and frame.height == 48
        for frame in walk_left.frames
    )

    idle_up = sheet.animations[7]

    assert [frame.column for frame in idle_up.frames] == [0, 1]
    assert [(frame.x, frame.y) for frame in idle_up.frames] == [
        (0, 336),
        (48, 336),
    ]

    damaged = sheet.animations[8]

    assert [(frame.x, frame.y) for frame in damaged.frames] == [
        (0, 384),
        (48, 384),
        (96, 384),
    ]


def test_animation_speeds_and_loops_follow_the_layout() -> None:
    conversion = CharacterSpriteSheetBuilder().convert(build_analysis())

    sheet = conversion.sheets[0]

    for animation, spec in zip(sheet.animations, CHARACTER_ANIMATIONS):
        assert animation.name == spec.name
        assert animation.speed == spec.speed
        assert animation.loop == spec.loop

    speeds = {
        animation.name: animation.speed
        for animation in sheet.animations
    }
    loops = {
        animation.name: animation.loop
        for animation in sheet.animations
    }

    assert speeds["walk-down"] == WALK_FPS
    assert speeds["idle-down"] == IDLE_FPS
    assert speeds["damaged"] == DAMAGED_FPS

    assert loops["walk-up"] is True
    assert loops["idle-up"] is True
    assert loops["damaged"] is False
