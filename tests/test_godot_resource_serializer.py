from dataclasses import replace

from rpgmaker2godot.godot.model import GodotAtlasTileResource
from rpgmaker2godot.godot.resource.resource_serializer import (
    GodotResourceSerializer,
)
from rpgmaker2godot.godot.tileset.collision import GodotTileCollision

from tests.helpers.godot_resource import make_resource
from tests.helpers.godot_tileset import make_godot_tileset_resource


def test_serializes_godot_resource_header() -> None:
    content = GodotResourceSerializer().serialize(
        make_resource()
    )

    assert (
        '[gd_resource type="TileSet" load_steps=3 format=3]'
        in content
    )


def test_serializes_texture_ext_resource() -> None:
    content = GodotResourceSerializer().serialize(
        make_resource()
    )

    assert (
        '[ext_resource type="Texture2D" '
        'path="res://Inside.png" id="1_texture"]'
        in content
    )


def test_serializes_atlas_source() -> None:
    content = GodotResourceSerializer().serialize(
        make_resource()
    )

    assert (
        '[sub_resource type="TileSetAtlasSource" '
        'id="TileSetAtlasSource_1"]'
        in content
    )


def test_serializes_texture_region_size() -> None:
    content = GodotResourceSerializer().serialize(
        make_resource()
    )

    assert (
        "texture_region_size = Vector2i(48, 48)"
        in content
    )


def test_serializes_atlas_cells() -> None:
    content = GodotResourceSerializer().serialize(
        make_resource()
    )

    assert "0:0/0 = 0" in content
    assert "1:0/0 = 0" in content
    assert "0:1/0 = 0" in content
    assert "1:1/0 = 0" in content


def test_serializes_tileset_resource() -> None:
    content = GodotResourceSerializer().serialize(
        make_resource()
    )

    assert "[resource]" in content
    assert "tile_size = Vector2i(48, 48)" in content
    assert (
        'sources/0 = SubResource("TileSetAtlasSource_1")'
        in content
    )


def test_serializes_two_by_one_atlas_tile() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                width=2,
                height=1,
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    assert "0:0/0 = 0" in content


def test_serializes_one_by_two_atlas_tile() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                width=1,
                height=2,
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    assert "0:0/0 = 0" in content


def test_serializes_two_by_three_atlas_tile() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                width=2,
                height=3,
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    assert "0:0/0 = 0" in content


def test_serializes_multi_cell_tile_size() -> None:
    resource = make_godot_tileset_resource()

    atlas = replace(
        resource.atlas_source,
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                width=2,
                height=1,
            ),
            GodotAtlasTileResource(
                column=1,
                row=0,
                width=1,
                height=2,
            ),
            GodotAtlasTileResource(
                column=0,
                row=1,
                width=2,
                height=3,
            ),
        ),
    )

    resource = replace(
        resource,
        atlas_source=atlas,
    )

    content = GodotResourceSerializer().serialize(resource)

    assert "0:0/0 = 0" in content
    assert "0:0/size_in_atlas = Vector2i(2, 1)" in content

    assert "1:0/0 = 0" in content
    assert "1:0/size_in_atlas = Vector2i(1, 2)" in content

    assert "0:1/0 = 0" in content
    assert "0:1/size_in_atlas = Vector2i(2, 3)" in content


def test_does_not_serialize_unit_tile_size() -> None:
    resource = make_godot_tileset_resource()

    content = GodotResourceSerializer().serialize(resource)

    assert "/size_in_atlas" not in content


def test_serializes_collision_polygon_points() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                collision=GodotTileCollision(
                    points=(
                        (0.0, 0.0),
                        (48.0, 0.0),
                        (48.0, 48.0),
                        (0.0, 48.0),
                    ),
                ),
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    assert (
        "0:0/0/physics_layer_0/polygon_0/points = "
        "PackedVector2Array(0, 0, 48, 0, 48, 48, 0, 48)"
    ) in content


def test_serializes_fractional_negative_coordinates() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=1,
                row=2,
                collision=GodotTileCollision(
                    points=(
                        (-23.5, -49.0),
                        (25.25, -49.0),
                        (25.25, 49.0),
                        (-23.5, 49.0),
                    ),
                ),
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    assert (
        "1:2/0/physics_layer_0/polygon_0/points = "
        "PackedVector2Array(-23.5, -49, 25.25, -49, 25.25, 49, -23.5, 49)"
    ) in content


def test_does_not_serialize_polygon_without_collision() -> None:
    resource = make_godot_tileset_resource()

    content = GodotResourceSerializer().serialize(resource)

    assert "/physics_layer_0/polygon" not in content
    assert "PackedVector2Array" not in content


def test_orders_cell_lines_like_godot() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                width=2,
                height=1,
                collision=GodotTileCollision(
                    points=(
                        (0.0, 0.0),
                        (96.0, 0.0),
                        (96.0, 48.0),
                        (0.0, 48.0),
                    ),
                ),
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    size_position = content.index("0:0/size_in_atlas")
    alternative_position = content.index("0:0/0 = 0")
    polygon_position = content.index(
        "0:0/0/physics_layer_0/polygon_0/points",
    )

    assert size_position < alternative_position < polygon_position


def test_serializes_one_polygon_per_colliding_tile() -> None:
    resource = make_godot_tileset_resource(
        tiles=(
            GodotAtlasTileResource(
                column=0,
                row=0,
                collision=GodotTileCollision(
                    points=(
                        (0.0, 0.0),
                        (48.0, 0.0),
                        (48.0, 24.0),
                        (0.0, 24.0),
                    ),
                ),
            ),
            GodotAtlasTileResource(
                column=1,
                row=0,
            ),
            GodotAtlasTileResource(
                column=0,
                row=1,
                collision=GodotTileCollision(
                    points=(
                        (0.0, 0.0),
                        (48.0, 0.0),
                        (48.0, 48.0),
                    ),
                ),
            ),
        ),
    )

    content = GodotResourceSerializer().serialize(resource)

    assert content.count("/physics_layer_0/polygon_0/points") == 2
    assert "0:0/0/physics_layer_0/polygon_0" in content
    assert "0:1/0/physics_layer_0/polygon_0" in content
    assert "1:0/0/physics_layer_0/polygon_0" not in content