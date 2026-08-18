from pathlib import Path

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.godot.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.tileset_builder import (
    GodotTileSetBuilder,
)
from rpgmaker2godot.model import SheetType

from tests.helpers.atlas import (
    make_sheet,
    make_tileset_with_sheets,
)


def test_builds_godot_tileset() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    result = GodotTileSetBuilder().build(
        mapping,
        Path("Inside.png"),
    )

    assert result.tile_width == 48
    assert result.tile_height == 48

    assert len(result.atlas_sources) == 1


def test_preserves_texture_path() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    result = GodotTileSetBuilder().build(
        mapping,
        Path("Inside.png"),
    )

    source = result.atlas_sources[0]

    assert source.texture_path == Path("Inside.png")


def test_preserves_atlas_dimensions() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    result = GodotTileSetBuilder().build(
        mapping,
        Path("Inside.png"),
    )

    source = result.atlas_sources[0]

    assert source.texture_width == 96
    assert source.texture_height == 96

    assert source.tile_width == 48
    assert source.tile_height == 48


def test_converts_pixel_coordinates_to_cells() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    result = GodotTileSetBuilder().build(
        mapping,
        Path("Inside.png"),
    )

    source = result.atlas_sources[0]

    assert [
        (tile.cell.column, tile.cell.row)
        for tile in source.tiles
        if tile.cell is not None
    ] == [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
    ]


def test_preserves_source_coordinates() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    result = GodotTileSetBuilder().build(
        mapping,
        Path("Inside.png"),
    )

    source = result.atlas_sources[0]

    assert [
        (tile.source_x, tile.source_y)
        for tile in source.tiles
    ] == [
        (0, 0),
        (48, 0),
        (0, 48),
        (48, 48),
    ]