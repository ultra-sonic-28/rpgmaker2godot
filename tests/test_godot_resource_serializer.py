from dataclasses import replace

from rpgmaker2godot.godot.model import GodotAtlasTileResource
from rpgmaker2godot.godot.resource_serializer import (
    GodotResourceSerializer,
)

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