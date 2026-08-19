from rpgmaker2godot.godot.atlas.atlas_builder import GodotAtlasSourceBuilder

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
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
    )


def test_preserves_tile_order():
    source = make_godot_atlas_source()

    result = GodotAtlasSourceBuilder().build(
        source,
        resource_id="Atlas",
        texture_resource_id="Texture",
    )

    assert result.tiles == tuple(
        (tile.cell.column, tile.cell.row)
        for tile in source.tiles
    )