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
    resource_path: str = "res://generated/Inside.tres",
    expected_atlas_size: tuple[int, int] = (96, 288),
    expected_columns: int = 2,
    expected_rows: int = 6,
    validate_all_cells: bool = True,
    expected_missing_cell: tuple[int, int] | None = None,
    expected_tile_sizes: tuple[
        tuple[tuple[int, int], tuple[int, int]],
        ...,
    ] | None = None,
    expected_collision_polygons: tuple[
        tuple[tuple[int, int], tuple[float, ...]],
        ...,
    ] | None = None,
    expected_collision_free_cells: tuple[
        tuple[int, int],
        ...,
    ] | None = None,
    expected_terrain_set_count: int | None = None,
    expected_terrain_modes: tuple[tuple[int, int], ...] | None = None,
    expected_terrain_names: tuple[tuple[int, str], ...] | None = None,
    expected_cell_terrains: tuple[
        tuple[tuple[int, int], int, int],
        ...,
    ] | None = None,
    expected_cell_peering_bits: tuple[
        tuple[tuple[int, int], tuple[tuple[str, int], ...]],
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

    collision_polygon_checks = ""

    if expected_collision_polygons is not None:
        polygon_checks: list[str] = []

        polygon_checks.append(
            """
    # -------------------------------------------------------------------------
    # Validate that the TileSet exposes a physics layer.
    # -------------------------------------------------------------------------
    if tileset.get_physics_layers_count() < 1:
        fail(
            "Expected at least one physics layer on the TileSet"
        )
        return
"""
        )

        for cell, points in expected_collision_polygons:
            column, row = cell

            pairs = list(zip(points[::2], points[1::2]))
            appends = "\n".join(
                f"    expected_points_{column}_{row}.append("
                f"Vector2({float(x)!r}, {float(y)!r}))"
                for x, y in pairs
            )

            polygon_checks.append(
                f"""
    # -------------------------------------------------------------------------
    # Validate the collision polygon at ({column}, {row}).
    # -------------------------------------------------------------------------
    if not atlas_source.has_tile(Vector2i({column}, {row})):
        fail(
            "Missing expected tile at Vector2i({column}, {row})"
        )
        return

    var data_{column}_{row} := (
        atlas_source.get_tile_data(Vector2i({column}, {row}), 0)
    )

    if data_{column}_{row} == null:
        fail(
            "Missing tile data at Vector2i({column}, {row})"
        )
        return

    if data_{column}_{row}.get_collision_polygons_count(0) != 1:
        fail(
            "Unexpected collision polygon count at Vector2i({column}, {row}): %d"
            % data_{column}_{row}.get_collision_polygons_count(0)
        )
        return

    var actual_points_{column}_{row} := (
        data_{column}_{row}.get_collision_polygon_points(0, 0)
    )
    var expected_points_{column}_{row} := PackedVector2Array()
{appends}

    if actual_points_{column}_{row}.size() != expected_points_{column}_{row}.size():
        fail(
            "Unexpected collision polygon size at Vector2i({column}, {row}): %d, must be %d"
            % [
                actual_points_{column}_{row}.size(),
                expected_points_{column}_{row}.size(),
            ]
        )
        return

    if actual_points_{column}_{row} != expected_points_{column}_{row}:
        fail(
            "Unexpected collision polygon at Vector2i({column}, {row}): %s, must be %s"
            % [
                actual_points_{column}_{row},
                expected_points_{column}_{row},
            ]
        )
        return
"""
            )

        collision_polygon_checks = "".join(polygon_checks)

    collision_free_checks = ""

    if expected_collision_free_cells is not None:
        free_entries: list[str] = []

        for cell in expected_collision_free_cells:
            column, row = cell

            free_entries.append(
                f"    validate_collision_free("
                f"atlas_source, Vector2i({column}, {row}))"
            )

        free_calls = "\n".join(free_entries)

        collision_free_checks = f"""
    # -------------------------------------------------------------------------
    # Validate that tiles without collision stay collision-free.
    # -------------------------------------------------------------------------
{free_calls}
"""

    terrain_checks = ""

    if expected_terrain_set_count is not None:
        terrain_checks += f"""
    # -------------------------------------------------------------------------
    # Validate the terrain set count.
    # -------------------------------------------------------------------------
    if tileset.get_terrain_sets_count() != {expected_terrain_set_count}:
        fail(
            "Unexpected terrain set count: %d"
            % tileset.get_terrain_sets_count()
        )
        return
"""

    if expected_terrain_modes is not None:
        for set_index, mode in expected_terrain_modes:
            terrain_checks += f"""
    if tileset.get_terrain_set_mode({set_index}) != {mode}:
        fail(
            "Unexpected mode for terrain set {set_index}: %d"
            % tileset.get_terrain_set_mode({set_index})
        )
        return
"""

    if expected_terrain_names is not None:
        for set_index, terrain_name in expected_terrain_names:
            terrain_checks += f"""
    if tileset.get_terrain_name({set_index}, 0) != "{terrain_name}":
        fail(
            "Unexpected terrain name for set {set_index}: %s"
            % tileset.get_terrain_name({set_index}, 0)
        )
        return
"""

    if expected_cell_terrains is not None:
        for cell, set_index, terrain_index in expected_cell_terrains:
            column, row = cell

            terrain_checks += f"""
    var cell_terrain_data_{column}_{row} := (
        atlas_source.get_tile_data(Vector2i({column}, {row}), 0)
    )

    if cell_terrain_data_{column}_{row} == null:
        fail("Missing tile data at Vector2i({column}, {row})")
        return

    if cell_terrain_data_{column}_{row}.get_terrain_set() != {set_index}:
        fail(
            "Unexpected terrain set at Vector2i({column}, {row}): %d"
            % cell_terrain_data_{column}_{row}.get_terrain_set()
        )
        return

    if cell_terrain_data_{column}_{row}.get_terrain() != {terrain_index}:
        fail(
            "Unexpected terrain at Vector2i({column}, {row}): %d"
            % cell_terrain_data_{column}_{row}.get_terrain()
        )
        return
"""

    if expected_cell_peering_bits is not None:
        peering_enum = {
            "right_side": "TileSet.CELL_NEIGHBOR_RIGHT_SIDE",
            "bottom_right_corner": "TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER",
            "bottom_side": "TileSet.CELL_NEIGHBOR_BOTTOM_SIDE",
            "bottom_left_corner": "TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER",
            "left_side": "TileSet.CELL_NEIGHBOR_LEFT_SIDE",
            "top_left_corner": "TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER",
            "top_side": "TileSet.CELL_NEIGHBOR_TOP_SIDE",
            "top_right_corner": "TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER",
        }

        for cell, bits in expected_cell_peering_bits:
            column, row = cell

            bit_checks = ""

            for bit_name, expected_value in bits:
                bit_checks += f"""
    if cell_peering_data_{column}_{row}.get_terrain_peering_bit(
        {peering_enum[bit_name]}
    ) != {expected_value}:
        fail(
            "Unexpected peering bit {bit_name} at Vector2i({column}, {row}): %d"
            % cell_peering_data_{column}_{row}.get_terrain_peering_bit(
                {peering_enum[bit_name]}
            )
        )
        return
"""

            terrain_checks += f"""
    if not atlas_source.has_tile(Vector2i({column}, {row})):
        fail("Missing tile at Vector2i({column}, {row})")
        return

    var cell_peering_data_{column}_{row} := (
        atlas_source.get_tile_data(Vector2i({column}, {row}), 0)
    )

    if cell_peering_data_{column}_{row} == null:
        fail("Missing tile data at Vector2i({column}, {row})")
        return
{bit_checks}"""

    script_path.write_text(
        f"""\
extends SceneTree

func fail(message: String) -> void:
    push_error(message)
    quit(1)


func validate_collision_free(
    source: TileSetAtlasSource,
    cell: Vector2i,
) -> void:
    if not source.has_tile(cell):
        fail(
            "Missing expected tile at %s"
            % cell
        )
        return

    var data := source.get_tile_data(cell, 0)

    if data == null:
        fail(
            "Missing tile data at %s"
            % cell
        )
        return

    if data.get_collision_polygons_count(0) != 0:
        fail(
            "Unexpected collision polygons at %s: %d"
            % [cell, data.get_collision_polygons_count(0)]
        )
        return


func _initialize() -> void:
    var resource = load("{resource_path}")

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
{collision_polygon_checks}
{collision_free_checks}
{tile_size_checks}
{terrain_checks}
    quit(0)
""",
        encoding="utf-8",
    )

    return script_path