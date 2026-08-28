from dataclasses import replace

import pytest

from rpgmaker2godot.godot.atlas.atlas_builder import GodotAtlasSourceBuilder
from rpgmaker2godot.godot.model import GodotAtlasCell, GodotAtlasTileResource
from rpgmaker2godot.godot.resource.resource import GodotAtlasSourceResource
from tests.helpers.godot_atlas import make_godot_atlas_source


def test_builds_atlas_source():
    source = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        source,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    assert result.resource_id == "TileSetAtlasSource_1"
    assert result.texture_resource_id == "1_texture"


def test_preserves_tile_size():
    source = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        source,
        resource_id="Atlas",
        texture_resource_id="Texture",
    )

    assert result.tile_width == source.tile_width
    assert result.tile_height == source.tile_height


def test_maps_tiles_to_cells():
    source = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        source,
        resource_id="Atlas",
        texture_resource_id="Texture",
    )

    assert result.tiles == (
        GodotAtlasTileResource(column=0, row=0),
        GodotAtlasTileResource(column=1, row=0),
        GodotAtlasTileResource(column=0, row=1),
        GodotAtlasTileResource(column=1, row=1),
    )


def test_preserves_tile_order():
    source = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        source,
        resource_id="Atlas",
        texture_resource_id="Texture",
    )

    assert result.tiles == tuple(
        GodotAtlasTileResource(column=tile.cell.column, row=tile.cell.row)
        for tile in source.tiles
    )


def test_preserves_missing_atlas_cell() -> None:
    atlas = make_godot_atlas_source()

    missing_cell = atlas.tiles[-1].cell

    tiles = tuple(
        tile
        for tile in atlas.tiles
        if tile.cell != missing_cell
    )

    atlas = replace(
        atlas,
        tiles=tiles,
    )

    result = GodotAtlasSourceBuilder().build(
        atlas,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    expected_tiles = tuple(
        GodotAtlasTileResource(column=tile.cell.column, row=tile.cell.row)
        for tile in tiles
    )

    assert result.tiles == expected_tiles
    assert (
        missing_cell.column,
        missing_cell.row,
    ) not in result.tiles


def test_atlas_source_resource_preserves_tile_cells() -> None:
    resource = GodotAtlasSourceResource(
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
        tile_width=48,
        tile_height=48,
        tiles=(
            GodotAtlasTileResource(column=0, row=0),
            GodotAtlasTileResource(column=1, row=0),
            GodotAtlasTileResource(column=0, row=1),
        ),
    )

    assert resource.tiles == (
        GodotAtlasTileResource(column=0, row=0),
        GodotAtlasTileResource(column=1, row=0),
        GodotAtlasTileResource(column=0, row=1),
    )


def test_builds_tile_resources() -> None:
    source = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        source,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    assert result.tiles == (
        GodotAtlasTileResource(column=0, row=0),
        GodotAtlasTileResource(column=1, row=0),
        GodotAtlasTileResource(column=0, row=1),
        GodotAtlasTileResource(column=1, row=1),
    )


def test_maps_tile_dimensions() -> None:
    atlas = make_godot_atlas_source()

    tile = atlas.tiles[0]

    modified_tile = replace(
        tile,
        width=96,
        height=144,
    )

    atlas = replace(
        atlas,
        tiles=(
            modified_tile,
            *atlas.tiles[1:],
        ),
    )

    result = GodotAtlasSourceBuilder().build(
        atlas,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    assert result.tiles[0] == GodotAtlasTileResource(
        column=0,
        row=0,
        width=2,
        height=3,
    )


def test_maps_unit_tile_dimensions() -> None:
    atlas = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        atlas,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    assert all(
        tile.width == 1 and tile.height == 1
        for tile in result.tiles
    )


def test_maps_non_unit_tile_dimensions() -> None:
    atlas = make_godot_atlas_source()

    source_tile = atlas.tiles[0]

    modified_tile = replace(
        source_tile,
        width=96,
        height=144,
    )

    atlas = replace(
        atlas,
        tiles=(
            modified_tile,
            *atlas.tiles[1:],
        ),
    )

    result = GodotAtlasSourceBuilder().build(
        atlas,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    assert result.tiles[0] == GodotAtlasTileResource(
        column=source_tile.cell.column,
        row=source_tile.cell.row,
        width=2,
        height=3,
    )


def test_propagate_maps_tile_dimensions() -> None:
    atlas = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        atlas,
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
    )

    assert [
        (
            tile.column,
            tile.row,
            tile.width,
            tile.height,
        )
        for tile in result.tiles
    ] == [
        (
            tile.cell.column,
            tile.cell.row,
            tile.width // atlas.tile_width,
            tile.height // atlas.tile_height,
        )
        for tile in atlas.tiles
    ]


def test_rejects_misaligned_tile_width() -> None:
    atlas = make_godot_atlas_source()

    tile = replace(
        atlas.tiles[0],
        width=50,
    )

    atlas = replace(
        atlas,
        tiles=(tile, *atlas.tiles[1:]),
    )

    with pytest.raises(ValueError, match="aligned"):
        GodotAtlasSourceBuilder().build(
            atlas,
            resource_id="TileSetAtlasSource_1",
            texture_resource_id="1_texture",
        )


def test_rejects_misaligned_tile_height() -> None:
    atlas = make_godot_atlas_source()

    tile = replace(
        atlas.tiles[0],
        height=50,
    )

    atlas = replace(
        atlas,
        tiles=(tile, *atlas.tiles[1:]),
    )

    with pytest.raises(ValueError, match="aligned"):
        GodotAtlasSourceBuilder().build(
            atlas,
            resource_id="TileSetAtlasSource_1",
            texture_resource_id="1_texture",
        )