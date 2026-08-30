"""Terrain serialization inside the Godot TileSet resource."""

from rpgmaker2godot.godot.model import (
    GodotAtlasTileResource,
    GodotTerrain,
    GodotTerrainSet,
    GodotTileTerrain,
)
from rpgmaker2godot.godot.resource.resource import (
    GodotAtlasSourceResource,
    GodotExtResource,
    GodotTileSetResource,
)
from rpgmaker2godot.godot.resource.resource_serializer import (
    GodotResourceSerializer,
)


def make_terrain_resource():
    return GodotTileSetResource(
        tile_width=48,
        tile_height=48,
        texture=GodotExtResource(
            resource_id="1_texture",
            resource_type="Texture2D",
            path="res://Inside.png",
        ),
        atlas_source=GodotAtlasSourceResource(
            resource_id="TileSetAtlasSource_1",
            texture_resource_id="1_texture",
            tile_width=48,
            tile_height=48,
            tiles=(
                GodotAtlasTileResource(
                    column=0,
                    row=0,
                    terrain=GodotTileTerrain(
                        set_index=0,
                        terrain_index=0,
                        peering_bits=(
                            ("right_side", 0),
                            ("bottom_side", 0),
                        ),
                    ),
                ),
            ),
        ),
        terrain_sets=(
            GodotTerrainSet(
                mode=0,
                terrains=(
                    GodotTerrain(
                        name="Wall top 1",
                        color=(1.0, 0.5, 0.25),
                    ),
                ),
            ),
        ),
    )


def test_serializes_terrain_set_declaration() -> None:
    content = GodotResourceSerializer().serialize(
        make_terrain_resource()
    )

    assert "terrain_set_0/mode = 0" in content
    assert 'terrain_set_0/terrain_0/name = "Wall top 1"' in content
    assert (
        "terrain_set_0/terrain_0/color = Color(1, 0.5, 0.25, 1)"
        in content
    )


def test_serializes_tile_terrain_assignment() -> None:
    content = GodotResourceSerializer().serialize(
        make_terrain_resource()
    )

    assert "0:0/0/terrain_set = 0" in content
    assert "0:0/0/terrain = 0" in content
    assert "0:0/0/terrains_peering_bit/right_side = 0" in content
    assert "0:0/0/terrains_peering_bit/bottom_side = 0" in content


def test_terrain_properties_follow_the_cell_declaration() -> None:
    content = GodotResourceSerializer().serialize(
        make_terrain_resource()
    )

    cell_position = content.index("0:0/0 = 0")
    terrain_position = content.index("0:0/0/terrain_set = 0")
    bit_position = content.index(
        "0:0/0/terrains_peering_bit/right_side = 0"
    )

    assert cell_position < terrain_position < bit_position


def test_resource_without_terrains_stays_unchanged() -> None:
    from tests.helpers.godot_resource import make_resource

    content = GodotResourceSerializer().serialize(make_resource())

    assert "terrain_set_0/mode" not in content
    assert "terrains_peering_bit" not in content