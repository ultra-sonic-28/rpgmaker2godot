import subprocess
from pathlib import Path

import pytest
from PIL import Image

from rpgmaker2godot.analysis.character_detector import CharacterDetector
from rpgmaker2godot.character.spritesheet_builder import (
    CharacterSpriteSheetBuilder,
)
from rpgmaker2godot.godot.export.characters import CharacterExporter
from tests.helpers.godot_integration import find_godot, write_project
from tests.test_character_cli import create_character_sheet


def write_character_validation_script(
    project_directory: Path,
) -> Path:
    """Write the GDScript validating the generated SpriteFrames."""

    script_path = project_directory / "validate_characters.gd"

    lines = [
                "extends SceneTree",
                "",
                "",
                "func fail(message: String) -> void:",
                "\tpush_error(message)",
                "\tquit(1)",
                "",
                "",
                "func _initialize() -> void:",
                '\tvar resource = load("res://generated/player-1.tres")',
                "",
                "\tif resource == null:",
                '\t\tfail("Failed to load generated SpriteFrames")',
                "\t\treturn",
                "",
                "\tif not resource is SpriteFrames:",
                '\t\tfail("Generated resource is not a SpriteFrames")',
                "\t\treturn",
                "",
                "\tvar frames := resource as SpriteFrames",
                "\tvar expected := {",
                '\t\t"walk-down": [3, 6.0, true],',
                '\t\t"walk-left": [3, 6.0, true],',
                '\t\t"walk-right": [3, 6.0, true],',
                '\t\t"walk-up": [3, 6.0, true],',
                '\t\t"idle-down": [2, 2.0, true],',
                '\t\t"idle-left": [2, 2.0, true],',
                '\t\t"idle-right": [2, 2.0, true],',
                '\t\t"idle-up": [2, 2.0, true],',
                '\t\t"damaged": [3, 8.0, false],',
                "\t}",
                "",
                "\tif frames.get_animation_names().size() != 9:",
                '\t\tfail("Expected 9 animations, got %d" % frames.get_animation_names().size())',
                "\t\treturn",
                "",
                "\tfor animation_name in expected:",
                "\t\tvar spec = expected[animation_name]",
                "",
                "\t\tif not frames.has_animation(animation_name):",
                '\t\t\tfail("Missing animation: %s" % animation_name)',
                "\t\t\treturn",
                "",
                "\t\tif frames.get_frame_count(animation_name) != spec[0]:",
                '\t\t\tfail("Wrong frame count for %s" % animation_name)',
                "\t\t\treturn",
                "",
                "\t\tif frames.get_animation_speed(animation_name) != spec[1]:",
                '\t\t\tfail("Wrong speed for %s" % animation_name)',
                "\t\t\treturn",
                "",
                "\t\tif frames.get_animation_loop(animation_name) != spec[2]:",
                '\t\t\tfail("Wrong loop for %s" % animation_name)',
                "\t\t\treturn",
                "",
                '\t\tif not frames.get_frame_texture(animation_name, 0) is AtlasTexture:',
                '\t\t\tfail("Frame 0 of %s is not an AtlasTexture" % animation_name)',
                "\t\t\treturn",
                "",
                '\tvar region = (frames.get_frame_texture("idle-up", 1) as AtlasTexture).region',
                "",
                "\tif region != Rect2(48, 336, 48, 48):",
                '\t\tfail("Unexpected idle-up frame 1 region: %s" % region)',
                "\t\treturn",
                "",
                '\tprint("CHARACTER_RESOURCE_OK")',
                "\tquit(0)",
    ]

    script_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    return script_path


@pytest.mark.integration
def test_generated_character_loads_in_godot(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    input_directory = tmp_path / "characters"
    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_character_sheet(
        input_directory,
        "player-1.png",
        frame_size=(48, 48),
    )

    analysis = CharacterDetector().analyze(
        input_directory,
    )

    conversion = CharacterSpriteSheetBuilder().convert(
        analysis,
    )

    CharacterExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    script_path = write_character_validation_script(
        project_directory,
    )

    generated_png = generated_directory / "player-1.png"
    assert generated_png.exists()
    assert generated_png.stat().st_size > 0

    with Image.open(generated_png) as image:
        image.verify()

    generated_tres = generated_directory / "player-1.tres"
    assert generated_tres.exists()
    assert generated_tres.stat().st_size > 0

    content = generated_tres.read_text(encoding="utf-8")

    assert (
        'path="res://generated/player-1.png"'
        in content
    )

    subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--editor",
            "--quit",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project_directory),
            "--script",
            str(script_path.name),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    print("VALIDATION STDOUT:")
    print(result.stdout)

    print("VALIDATION STDERR:")
    print(result.stderr)

    assert result.returncode == 0, (
        "Godot failed to validate the generated SpriteFrames.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )
