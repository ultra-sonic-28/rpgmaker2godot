from pathlib import Path
import pytest

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.godot.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.tileset_builder import (
    GodotTileSetBuilder,
)
from rpgmaker2godot.model import SheetType

from tests.helpers.godot_atlas import (
    make_mapping_with_tile, 
)

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


def test_maps_multiple_sheets_to_atlas_rows() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.C, 96, 96),
        make_sheet(SheetType.A5, 96, 96),
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
        (
            tile.ref.sheet_type,
            tile.cell.column,
            tile.cell.row,
        )
        for tile in source.tiles
        if tile.ref.index == 0
    ] == [
        (SheetType.A5, 0, 0),
        (SheetType.B, 0, 2),
        (SheetType.C, 0, 4),
    ]


def test_rejects_misaligned_horizontal_tile() -> None:
    mapping = make_mapping_with_tile(
        atlas_x=49,
        atlas_y=0,
    )

    with pytest.raises(
        ValueError,
        match="not aligned to the atlas grid horizontally",
    ):
        GodotTileSetBuilder().build(
            mapping,
            Path("Inside.png"),
        )


def test_rejects_misaligned_vertical_tile() -> None:
    mapping = make_mapping_with_tile(
        atlas_x=0,
        atlas_y=49,
    )

    with pytest.raises(
        ValueError,
        match="not aligned to the atlas grid vertically",
    ):
        GodotTileSetBuilder().build(
            mapping,
            Path("Inside.png"),
        )


def test_rejects_tile_outside_atlas_horizontally() -> None:
    mapping = make_mapping_with_tile(
        atlas_x=96,
        atlas_y=0,
    )

    with pytest.raises(
        ValueError,
        match="outside atlas horizontally",
    ):
        GodotTileSetBuilder().build(
            mapping,
            Path("Inside.png"),
        )


def test_rejects_tile_outside_atlas_vertically() -> None:
    mapping = make_mapping_with_tile(
        atlas_x=0,
        atlas_y=96,
    )

    with pytest.raises(
        ValueError,
        match="outside atlas vertically",
    ):
        GodotTileSetBuilder().build(
            mapping,
            Path("Inside.png"),
        )