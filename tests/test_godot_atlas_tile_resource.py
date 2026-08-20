import pytest

from rpgmaker2godot.godot.atlas.atlas_builder import GodotAtlasSourceBuilder
from rpgmaker2godot.godot.model import (
    GodotAtlasTileResource,
)
from tests.helpers.godot_atlas import make_godot_atlas_source


def test_creates_unit_tile() -> None:
    tile = GodotAtlasTileResource(
        column=1,
        row=3,
    )

    assert tile.column == 1
    assert tile.row == 3
    assert tile.width == 1
    assert tile.height == 1


def test_creates_multi_cell_tile() -> None:
    tile = GodotAtlasTileResource(
        column=2,
        row=4,
        width=2,
        height=3,
    )

    assert tile.column == 2
    assert tile.row == 4
    assert tile.width == 2
    assert tile.height == 3


def test_rejects_negative_column() -> None:
    with pytest.raises(
        ValueError,
        match="column",
    ):
        GodotAtlasTileResource(
            column=-1,
            row=0,
        )


def test_rejects_negative_row() -> None:
    with pytest.raises(
        ValueError,
        match="row",
    ):
        GodotAtlasTileResource(
            column=0,
            row=-1,
        )


def test_rejects_zero_width() -> None:
    with pytest.raises(
        ValueError,
        match="width",
    ):
        GodotAtlasTileResource(
            column=0,
            row=0,
            width=0,
        )


def test_rejects_negative_width() -> None:
    with pytest.raises(
        ValueError,
        match="width",
    ):
        GodotAtlasTileResource(
            column=0,
            row=0,
            width=-1,
        )


def test_rejects_zero_height() -> None:
    with pytest.raises(
        ValueError,
        match="height",
    ):
        GodotAtlasTileResource(
            column=0,
            row=0,
            height=0,
        )


def test_rejects_negative_height() -> None:
    with pytest.raises(
        ValueError,
        match="height",
    ):
        GodotAtlasTileResource(
            column=0,
            row=0,
            height=-1,
        )


def test_maps_tile_dimensions_to_unit_size() -> None:
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