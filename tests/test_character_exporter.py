from pathlib import Path

from PIL import Image

from rpgmaker2godot.character.models import (
    CharacterAnimation,
    CharacterConversionResult,
    CharacterFrame,
    CharacterSpriteSheet,
)
from rpgmaker2godot.godot.export.characters import CharacterExporter


def create_source_sheet(
    directory: Path,
    filename: str,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (144, 432), (10, 20, 30, 255))
    image.save(directory / filename)

    return directory / filename


def build_conversion(
    source_path: Path,
) -> CharacterConversionResult:
    sheet = CharacterSpriteSheet(
        name="player-1",
        source_path=source_path,
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
                    CharacterFrame(
                        column=2,
                        row=0,
                        x=96,
                        y=0,
                        width=48,
                        height=48,
                    ),
                ),
            ),
            CharacterAnimation(
                name="damaged",
                speed=8.0,
                loop=False,
                frames=(
                    CharacterFrame(
                        column=0,
                        row=8,
                        x=0,
                        y=384,
                        width=48,
                        height=48,
                    ),
                ),
            ),
        ),
    )

    return CharacterConversionResult(sheets=(sheet,))


def test_exports_the_png_and_the_resource(tmp_path: Path) -> None:
    source_path = create_source_sheet(tmp_path / "src", "player-1.png")
    output_directory = tmp_path / "output"

    generated = CharacterExporter().export(
        build_conversion(source_path),
        output_directory,
    )

    texture_path = output_directory / "player-1.png"
    resource_path = output_directory / "player-1.tres"

    assert generated == (texture_path, resource_path)

    assert texture_path.exists()
    assert resource_path.exists()

    with Image.open(texture_path) as image:
        assert image.size == (144, 432)
        assert image.getpixel((0, 0)) == (10, 20, 30, 255)

    content = resource_path.read_text(encoding="utf-8")

    assert '[gd_resource type="SpriteFrames"' in content
    assert 'path="res://player-1.png"' in content
    assert '"name": &"walk-down",' in content
    assert '"name": &"damaged",' in content


def test_creates_the_output_directory(tmp_path: Path) -> None:
    source_path = create_source_sheet(tmp_path / "src", "player-1.png")
    output_directory = tmp_path / "output" / "characters"

    CharacterExporter().export(
        build_conversion(source_path),
        output_directory,
    )

    assert (output_directory / "player-1.png").exists()
    assert (output_directory / "player-1.tres").exists()


def test_exports_every_character_of_the_conversion(tmp_path: Path) -> None:
    source_path = create_source_sheet(tmp_path / "src", "player-1.png")

    conversion = build_conversion(source_path)

    npc_sheet = CharacterSpriteSheet(
        name="npc-1",
        source_path=source_path,
        width=144,
        height=432,
        frame_width=48,
        frame_height=48,
        animations=conversion.sheets[0].animations,
    )

    conversion = CharacterConversionResult(
        sheets=(conversion.sheets[0], npc_sheet),
    )

    output_directory = tmp_path / "output"

    generated = CharacterExporter().export(
        conversion,
        output_directory,
    )

    assert generated == (
        output_directory / "player-1.png",
        output_directory / "player-1.tres",
        output_directory / "npc-1.png",
        output_directory / "npc-1.tres",
    )


def test_uses_the_godot_project_root_for_the_texture_path(
    tmp_path: Path,
) -> None:
    source_path = create_source_sheet(tmp_path / "src", "player-1.png")

    project_directory = tmp_path / "godot"
    output_directory = project_directory / "generated"

    CharacterExporter(
        godot_project_root=project_directory,
    ).export(
        build_conversion(source_path),
        output_directory,
    )

    content = (output_directory / "player-1.tres").read_text(
        encoding="utf-8",
    )

    assert 'path="res://generated/player-1.png"' in content
