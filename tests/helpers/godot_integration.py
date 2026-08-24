"""Shared helpers for the Godot integration test-suite."""

import os
import subprocess
from pathlib import Path


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