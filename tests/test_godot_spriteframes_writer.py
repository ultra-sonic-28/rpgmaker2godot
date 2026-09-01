from pathlib import Path

import pytest

from rpgmaker2godot.character.models import (
    CharacterAnimation,
    CharacterFrame,
    CharacterSpriteSheet,
)
from rpgmaker2godot.godot.spriteframes.writer import GodotSpriteFramesWriter


def build_sheet() -> CharacterSpriteSheet:
    return CharacterSpriteSheet(
        name="player-1",
        source_path=Path("characters/player-1.png"),
        width=144,
        height=432,
        frame_width=48,
        frame_height=48,
        animations=(
            CharacterAnimation(
                name="walk-down",
                speed=6.0,
                loop=True,
                frames=(
                    CharacterFrame(
                        column=0,
                        row=0,
                        x=0,
                        y=0,
                        width=48,
                        height=48,
                    ),
                    CharacterFrame(
                        column=1,
                        row=0,
                        x=48,
                        y=0,
                        width=48,
                        height=48,
                    ),
                ),
            ),
            CharacterAnimation(
                name="idle-down",
                speed=2.0,
                loop=True,
                frames=(
                    CharacterFrame(
                        column=0,
                        row=4,
                        x=0,
                        y=192,
                        width=48,
                        height=48,
                    ),
                ),
            ),
        ),
    )


def test_writes_a_spriteframes_resource(tmp_path: Path) -> None:
    output_path = tmp_path / "player-1.tres"

    GodotSpriteFramesWriter().write(
        build_sheet(),
        output_path,
        Path("player-1.png"),
    )

    content = output_path.read_text(encoding="utf-8")

    # 3 AtlasTexture sub-resources + 1 ext_resource + the resource.
    assert (
        '[gd_resource type="SpriteFrames" load_steps=5 format=3]'
        in content
    )
    assert 'path="res://player-1.png"' in content
    assert "region = Rect2(48, 0, 48, 48)" in content
    assert "region = Rect2(0, 192, 48, 48)" in content
    assert '"name": &"walk-down",' in content
    assert '"name": &"idle-down",' in content


def test_numbers_frames_across_animations(tmp_path: Path) -> None:
    output_path = tmp_path / "player-1.tres"

    GodotSpriteFramesWriter().write(
        build_sheet(),
        output_path,
        Path("player-1.png"),
    )

    content = output_path.read_text(encoding="utf-8")

    assert 'id="AtlasTexture_1"' in content
    assert 'id="AtlasTexture_2"' in content
    assert 'id="AtlasTexture_3"' in content


def test_creates_the_output_directory(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "player-1.tres"

    GodotSpriteFramesWriter().write(
        build_sheet(),
        output_path,
        Path("player-1.png"),
    )

    assert output_path.exists()


def test_preserves_a_godot_texture_path(tmp_path: Path) -> None:
    output_path = tmp_path / "player-1.tres"

    GodotSpriteFramesWriter().write(
        build_sheet(),
        output_path,
        Path("res://assets/player-1.png"),
    )

    content = output_path.read_text(encoding="utf-8")

    assert 'path="res://assets/player-1.png"' in content


def test_converts_an_absolute_texture_path_inside_the_resource_directory(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "player-1.tres"

    GodotSpriteFramesWriter().write(
        build_sheet(),
        output_path,
        tmp_path / "player-1.png",
    )

    content = output_path.read_text(encoding="utf-8")

    assert 'path="res://player-1.png"' in content


def test_rejects_an_absolute_texture_path_outside_the_resource_directory(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "player-1.tres"

    # A path on the drive root can never live below tmp_path.
    outside_path = Path(tmp_path.anchor) / "elsewhere" / "player-1.png"

    with pytest.raises(ValueError):
        GodotSpriteFramesWriter().write(
            build_sheet(),
            output_path,
            outside_path,
        )
