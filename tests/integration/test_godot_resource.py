from dataclasses import replace
import os
import subprocess
from pathlib import Path

from PIL import Image
import pytest

from rpgmaker2godot.analysis.detector import TilesetDetector
from rpgmaker2godot.conversion.converter import SimpleConverter
from rpgmaker2godot.godot.export.simple import SimpleExporter
from tests.test_cli import create_sheet
from tests.helpers.godot_atlas import make_multi_cell_conversion


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
    *,
    expected_atlas_size: tuple[int, int] = (96, 288),
    expected_columns: int = 2,
    expected_rows: int = 6,
    validate_all_cells: bool = True,
    expected_missing_cell: tuple[int, int] | None = None,
    expected_tile_sizes: tuple[
        tuple[tuple[int, int], tuple[int, int]],
        ...,
    ] | None = None,
) -> Path:
    script_path = project_directory / "validate.gd"

    missing_cell_check = ""

    if expected_missing_cell is not None:
        column, row = expected_missing_cell

        missing_cell_check = f"""
    # -------------------------------------------------------------------------
    # Validate that the expected missing cell is indeed missing.
    # -------------------------------------------------------------------------
    var missing_cell := Vector2i({column}, {row})

    if atlas_source.has_tile(missing_cell):
        fail(
            "Unexpected tile at (%d, %d)"
            % [missing_cell.x, missing_cell.y]
        )
        return
"""

    tile_size_checks = ""

    if expected_tile_sizes is not None:
        checks: list[str] = []

        tile_size_checks_header = """
    # -------------------------------------------------------------------------
    # Validate that the expected tile sizes are preserved.
    # This is important for multi-cell tiles.
    # -------------------------------------------------------------------------
"""

        for cell, size in expected_tile_sizes:
            column, row = cell
            width, height = size

            checks.append(
                f"""
    # -------------------------------------------------------------------------
    # Validate tile size at ({column}, {row}).
    # -------------------------------------------------------------------------
    var expected_cell_{column}_{row} := Vector2i(
        {column},
        {row},
    )

    if not atlas_source.has_tile(expected_cell_{column}_{row}):
        fail(
            "Missing expected tile at %s"
            % expected_cell_{column}_{row}
        )
        return

    var actual_size_{column}_{row} := (
        atlas_source.get_tile_size_in_atlas(
            expected_cell_{column}_{row}
        )
    )

    if actual_size_{column}_{row} != Vector2i(
        {width},
        {height},
    ):
        fail(
            "Unexpected tile size at %s: %s, must be %s"
            % [
                expected_cell_{column}_{row},
                actual_size_{column}_{row},
                Vector2i({width}, {height}),
            ]
        )
        return
"""
            )

        tile_size_checks = "".join(checks)

    tile_size_checks = tile_size_checks_header + tile_size_checks if tile_size_checks else ""
    atlas_width, atlas_height = expected_atlas_size

    all_cells_validation = ""

    if validate_all_cells:
        all_cells_validation = f"""
    # -------------------------------------------------------------------------
    # Validate that all expected cells are present in the atlas.
    # -------------------------------------------------------------------------
    var expected_columns := {expected_columns}
    var expected_rows := {expected_rows}

    for row in range(expected_rows):
        for column in range(expected_columns):
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
"""

    script_path.write_text(
        f"""\
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

    if atlas_source.texture.get_width() != {atlas_width}:
        fail(
            "Unexpected atlas width: %d"
            % atlas_source.texture.get_width()
        )
        return

    if atlas_source.texture.get_height() != {atlas_height}:
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

{all_cells_validation}
{missing_cell_check}
{tile_size_checks}
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


@pytest.mark.integration
def test_generated_tileset_rejects_missing_atlas_cell(
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

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    generated_tres = generated_directory / "Inside.tres"

    content = generated_tres.read_text(
        encoding="utf-8",
    )

    # Remove deliberately one atlas cell.
    content = content.replace(
        "1:3/0 = 0\n",
        "",
    )

    generated_tres.write_text(
        content,
        encoding="utf-8",
    )

    script_path = write_validation_script(
        project_directory,
        validate_all_cells=False,
        expected_missing_cell=(1, 3),
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

    assert result.returncode == 0, (
        "Godot unexpectedly accepted a TileSet "
        "with a missing atlas cell.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_generated_tileset_preserves_multi_cell_tile_sizes(
    tmp_path: Path,
) -> None:
    godot = find_godot()

    if godot is None:
        pytest.skip(
            "Godot executable not available. "
            "Set the GODOT environment variable."
        )

    project_directory = tmp_path / "godot"
    generated_directory = project_directory / "generated"

    generated_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_path = tmp_path / "tilesets" / "Inside_A5.png"

    create_sheet(
        source_path.parent,
        source_path.name,
        size=(192, 288),
    )

    conversion = make_multi_cell_conversion(
        source_path,
    )

    SimpleExporter(
        godot_project_root=project_directory,
    ).export(
        conversion,
        generated_directory,
    )

    write_project(project_directory)

    script_path = write_validation_script(
        project_directory,
        expected_atlas_size=(192, 288),
        expected_columns=4,
        expected_rows=6,
        validate_all_cells=False,
        expected_tile_sizes=(
            ((0, 0), (2, 1)),
            ((2, 0), (1, 2)),
            ((0, 2), (2, 3)),
        ),
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

    assert result.returncode == 0, (
        "Godot failed to validate multi-cell TileSet.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )