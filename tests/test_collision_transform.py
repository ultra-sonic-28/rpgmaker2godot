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


FULL_TILE_RECTANGLE = (
    (0.0, 0.0),
    (48.0, 0.0),
    (48.0, 48.0),
    (0.0, 48.0),
)


def test_returns_none_when_tile_has_no_collision() -> None:
    result = tile_collision_to_godot(
        None,
        width=48,
        height=48,
    )

    assert result is None


def test_maps_semantic_collision_to_full_tile_rectangle() -> None:
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

    assert result == GodotTileCollision(points=FULL_TILE_RECTANGLE)


def test_rectangle_covers_multi_cell_dimensions() -> None:
    result = tile_collision_to_godot(
        TileCollision(
            block_down=True,
            block_left=True,
            block_right=True,
            block_up=True,
        ),
        width=96,
        height=144,
    )

    assert result == GodotTileCollision(
        points=(
            (0.0, 0.0),
            (96.0, 0.0),
            (96.0, 144.0),
            (0.0, 144.0),
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
    assert tile.collision == GodotTileCollision(points=FULL_TILE_RECTANGLE)


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