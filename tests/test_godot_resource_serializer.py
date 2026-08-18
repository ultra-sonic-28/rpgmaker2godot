from rpgmaker2godot.godot.resource_serializer import (
    GodotResourceSerializer,
)

from tests.helpers.godot_resource import make_resource


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