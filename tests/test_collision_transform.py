import logging
from pathlib import Path

from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement
from rpgmaker2godot.godot.atlas.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.collision.tile_collision import has_collision
from rpgmaker2godot.godot.tileset.collision import (
    GodotTileCollision,
    tile_collision_to_godot,
)
from rpgmaker2godot.model import SheetType, TileRef
from rpgmaker2godot.model.tile_collision import TileCollision


# Wall bands for a 48x48 tile, expressed around the tile center
# (Godot convention) with the default wall thickness of 8 px.
BOTTOM_WALL = (
    (-24.0, 16.0),
    (24.0, 16.0),
    (24.0, 24.0),
    (-24.0, 24.0),
)

TOP_WALL = (
    (-24.0, -24.0),
    (24.0, -24.0),
    (24.0, -16.0),
    (-24.0, -16.0),
)

LEFT_WALL = (
    (-24.0, -24.0),
    (-16.0, -24.0),
    (-16.0, 24.0),
    (-24.0, 24.0),
)

RIGHT_WALL = (
    (16.0, -24.0),
    (24.0, -24.0),
    (24.0, 24.0),
    (16.0, 24.0),
)

FULL_TILE_RECTANGLE = (
    (-24.0, -24.0),
    (24.0, -24.0),
    (24.0, 24.0),
    (-24.0, 24.0),
)


ALL_BLOCKED = TileCollision(
    block_down=True,
    block_left=True,
    block_right=True,
    block_up=True,
)

DOWN_ONLY = TileCollision(
    block_down=True,
    block_left=False,
    block_right=False,
    block_up=False,
)

DOWN_AND_LEFT = TileCollision(
    block_down=True,
    block_left=True,
    block_right=False,
    block_up=False,
)

UP_AND_DOWN = TileCollision(
    block_down=True,
    block_left=False,
    block_right=False,
    block_up=True,
)

LEFT_AND_RIGHT = TileCollision(
    block_down=False,
    block_left=True,
    block_right=True,
    block_up=False,
)

THREE_SIDES = TileCollision(
    block_down=True,
    block_left=True,
    block_right=True,
    block_up=False,
)


def test_returns_none_when_tile_has_no_collision() -> None:
    result = tile_collision_to_godot(
        None,
        width=48,
        height=48,
    )

    assert result is None


def test_maps_all_blocked_sides_to_full_covering_rectangle() -> None:
    result = tile_collision_to_godot(
        ALL_BLOCKED,
        width=48,
        height=48,
    )

    # Every side blocked means the tile is fully solid: one
    # rectangle covering the whole tile replaces the wall bands.
    assert result == GodotTileCollision(
        polygons=(FULL_TILE_RECTANGLE,),
    )


def test_blocks_single_side_as_one_wall_band() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=True,
            block_left=False,
            block_right=False,
            block_up=False,
        ),
        width=48,
        height=48,
    )

    assert result == GodotTileCollision(polygons=(BOTTOM_WALL,))


def test_two_adjacent_sides_produce_two_overlapping_walls() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=True,
            block_left=True,
            block_right=False,
            block_up=False,
        ),
        width=48,
        height=48,
    )

    # Bottom and left walls overlap in the lower-left corner;
    # their union forms the expected quarter-tile L shape.
    assert result == GodotTileCollision(
        polygons=(
            BOTTOM_WALL,
            LEFT_WALL,
        ),
    )


def test_opposite_vertical_pair_produces_top_and_bottom_walls() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=True,
            block_left=False,
            block_right=False,
            block_up=True,
        ),
        width=48,
        height=48,
    )

    assert result == GodotTileCollision(
        polygons=(
            BOTTOM_WALL,
            TOP_WALL,
        ),
    )


def test_opposite_horizontal_pair_produces_left_and_right_walls() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=False,
            block_left=True,
            block_right=True,
            block_up=False,
        ),
        width=48,
        height=48,
    )

    assert result == GodotTileCollision(
        polygons=(
            LEFT_WALL,
            RIGHT_WALL,
        ),
    )


def test_three_sides_produce_three_wall_bands() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=True,
            block_left=True,
            block_right=True,
            block_up=False,
        ),
        width=48,
        height=48,
    )

    assert result == GodotTileCollision(
        polygons=(
            BOTTOM_WALL,
            LEFT_WALL,
            RIGHT_WALL,
        ),
    )


def test_full_tile_rectangle_covers_multi_cell_dimensions() -> None:
    result = tile_collision_to_godot(
        ALL_BLOCKED,
        width=96,
        height=144,
    )

    assert result == GodotTileCollision(
        polygons=(
            (
                (-48.0, -72.0),
                (48.0, -72.0),
                (48.0, 72.0),
                (-48.0, 72.0),
            ),
        ),
    )


def _make_placement_with_collision(
    collision: TileCollision | None,
) -> AtlasPlacement:
    return AtlasPlacement(
        tile=TileRef(
            tileset="Inside",
            sheet_type=SheetType.B,
            index=0,
        ),
        source_path=Path("Inside_B.png"),
        source_x=0,
        source_y=0,
        atlas_x=0,
        atlas_y=0,
        width=48,
        height=48,
        collision=collision,
    )


def test_mapper_produces_godot_geometry_not_semantic_model() -> None:
    placement = _make_placement_with_collision(
        TileCollision(
            block_down=False,
            block_left=True,
            block_right=False,
            block_up=False,
        ),
    )

    mapping = GodotAtlasMapper().map(
        Atlas(
            width=48,
            height=48,
            tile_width=48,
            tile_height=48,
            placements=(placement,),
        ),
    )

    tile = mapping.tiles[0]

    assert isinstance(tile.collision, GodotTileCollision)

    # The mapper output uses the directional geometry: only the
    # left wall band is solid for a leftward-blocking tile.
    assert tile.collision == GodotTileCollision(polygons=(LEFT_WALL,))


def test_mapper_keeps_collision_free_tiles() -> None:
    placement = _make_placement_with_collision(None)

    mapping = GodotAtlasMapper().map(
        Atlas(
            width=48,
            height=48,
            tile_width=48,
            tile_height=48,
            placements=(placement,),
        ),
    )

    assert mapping.tiles[0].collision is None


def test_fully_passable_tile_stays_collision_free() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=False,
            block_left=False,
            block_right=False,
            block_up=False,
        ),
        width=48,
        height=48,
    )

    assert result is None


def test_has_collision_rejects_fully_passable_model() -> None:
    assert has_collision(None) is False

    assert (
        has_collision(
            TileCollision(
                block_down=False,
                block_left=False,
                block_right=False,
                block_up=False,
            ),
        )
        is False
    )

    assert (
        has_collision(
            TileCollision(
                block_down=True,
                block_left=False,
                block_right=False,
                block_up=False,
            ),
        )
        is True
    )


def test_logs_tile_coordinates_when_cell_provided(
    caplog,
) -> None:
    collision_logger = (
        "rpgmaker2godot.godot.tileset.collision"
    )

    with caplog.at_level(logging.DEBUG, logger=collision_logger):
        tile_collision_to_godot(
            TileCollision(
                block_down=True,
                block_left=False,
                block_right=False,
                block_up=False,
            ),
            width=48,
            height=48,
            cell=(3, 11),
        )

    messages = [record.getMessage() for record in caplog.records]

    assert any(
        "coord=(3, 11)" in message
        for message in messages
    )


def test_omits_coordinates_when_no_cell_provided(
    caplog,
) -> None:
    collision_logger = (
        "rpgmaker2godot.godot.tileset.collision"
    )

    with caplog.at_level(logging.DEBUG, logger=collision_logger):
        tile_collision_to_godot(
            TileCollision(
                block_down=True,
                block_left=True,
                block_right=True,
                block_up=False,
            ),
            width=48,
            height=48,
        )

    messages = [record.getMessage() for record in caplog.records]

    assert any("collision -> geometry" in message for message in messages)
    assert not any("coord=" in message for message in messages)