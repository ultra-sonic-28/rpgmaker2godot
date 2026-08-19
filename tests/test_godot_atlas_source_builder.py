from copy import replace

from rpgmaker2godot.godot.atlas.atlas_builder import GodotAtlasSourceBuilder

from rpgmaker2godot.godot.model import GodotAtlasCell, GodotAtlasTileResource
from rpgmaker2godot.godot.resource import GodotAtlasSourceResource
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