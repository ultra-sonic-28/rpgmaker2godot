import os
import subprocess
from pathlib import Path

from PIL import Image
import pytest

from rpgmaker2godot.analysis.detector import TilesetDetector
from rpgmaker2godot.conversion.converter import SimpleConverter
from rpgmaker2godot.export.simple import SimpleExporter
from tests.test_cli import create_sheet



def find_godot() -> str | None:
    configured = os.environ.get("GODOT")

    candidates = (
        (configured,) if configured else ()
    ) + (
        "godot",
        "godot4",
        "Godot_v4.7.1-stable_win64_console.exe"
    )

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            continue

        if result.returncode == 0:
            return candidate

    return None


def write_project(
    project_directory: Path,
) -> None:
    project_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (project_directory / "project.godot").write_text(
        """\
[application]

config/name="rpgmaker2godot-integration-test"

[display]

window/size/viewport_width=640
window/size/viewport_height=480

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
""",
        encoding="utf-8",
    )


def write_validation_script(
    project_directory: Path,
) -> Path:
    script_path = project_directory / "validate.gd"

    script_path.write_text(
        """\
extends SceneTree

func fail(message: String) -> void:
    push_error(message)
    quit(1)


func _initialize() -> void:
    var resource = load("res://generated/Inside.tres")

    if resource == null:
        fail("Failed to load generated TileSet")
        return

    if not resource is TileSet:
        fail("Generated resource is not a TileSet")
        return

    var tileset := resource as TileSet

    if tileset.tile_size != Vector2i(48, 48):
        fail(
            "Unexpected tile size: %s"
            % tileset.tile_size
        )
        return

    if tileset.get_source_count() != 1:
        fail(
            "Expected exactly one TileSet source, got %d"
            % tileset.get_source_count()
        )
        return

    var source = tileset.get_source(0)

    if not source is TileSetAtlasSource:
        fail("Source is not a TileSetAtlasSource")
        return

    var atlas_source := source as TileSetAtlasSource

    if atlas_source.texture == null:
        fail("Atlas source has no texture")
        return

    if atlas_source.texture.get_width() != 96:
        fail(
            "Unexpected atlas width: %d"
            % atlas_source.texture.get_width()
        )
        return

    if atlas_source.texture.get_height() != 288:
        fail(
            "Unexpected atlas height: %d"
            % atlas_source.texture.get_height()
        )
        return

    if atlas_source.texture_region_size != Vector2i(48, 48):
        fail(
            "Unexpected texture region size: %s"
            % atlas_source.texture_region_size
        )
        return

    for row in range(6):
        for column in range(2):
            var cell := Vector2i(column, row)

            if not atlas_source.has_tile(cell):
                fail(
                    "Missing tile at %s"
                    % cell
                )
                return
            
            var size := atlas_source.get_tile_size_in_atlas(cell)

            if size != Vector2i(1, 1):
                fail(
                    "Unexpected tile size at %s: %s"
                    % [cell, size]
                )
                return
                
    quit(0)
""",
        encoding="utf-8",
    )

    return script_path


@pytest.mark.integration
def test_generated_tileset_loads_in_godot(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    input_directory = tmp_path / "tilesets"
    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_sheet(
        input_directory,
        "Inside_A5.png",
    )

    create_sheet(
        input_directory,
        "Inside_B.png",
    )

    create_sheet(
        input_directory,
        "Inside_C.png",
    )

    analysis = TilesetDetector().analyze(
        input_directory,
    )

    conversion = SimpleConverter().convert(
        analysis,
    )

    SimpleExporter(godot_project_root=project_directory).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    script_path = write_validation_script(
        project_directory,
    )

    generated_png = generated_directory / "Inside.png"
    assert generated_png.exists()
    assert generated_png.stat().st_size > 0

    with Image.open(generated_png) as image:
        image.verify()
        
    generated_tres = generated_directory / "Inside.tres"
    assert generated_tres.exists()
    assert generated_tres.stat().st_size > 0

    content = generated_tres.read_text(encoding="utf-8")

    assert (
        'path="res://generated/Inside.png"'
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

    print("IMPORT STDOUT:")
    print(result.stdout)

    print("IMPORT STDERR:")
    print(result.stderr)

    import_file = generated_directory / "Inside.png.import"

    assert import_file.exists(), (
        "Godot did not import generated PNG.\n"
        f"Expected: {import_file}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    assert result.returncode == 0, (
        "Godot failed to load generated TileSet.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )