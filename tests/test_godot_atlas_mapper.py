from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.godot.atlas.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.model import SheetType
from tests.helpers.atlas import (
    make_sheet,
    make_tileset_with_sheets,
)


def test_maps_tiles_to_atlas_coordinates() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            96,
            96,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert len(mapping.tiles) == 4

    assert [
        (tile.atlas_x, tile.atlas_y)
        for tile in mapping.tiles
    ] == [
        (0, 0),
        (48, 0),
        (0, 48),
        (48, 48),
    ]


def test_mapper_does_not_create_godot_cells() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    assert all(
        tile.cell is None
        for tile in mapping.tiles
    )

    
def test_maps_source_coordinates() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)
    mapping = GodotAtlasMapper().map(atlas)

    assert [
        (tile.source_x, tile.source_y)
        for tile in mapping.tiles
    ] == [
        (0, 0),
        (48, 0),
        (0, 48),
        (48, 48),
    ]


def test_preserves_tile_refs() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            96,
            96,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert [
        tile.ref
        for tile in mapping.tiles
    ] == [
        placement.tile
        for placement in atlas.placements
    ]


def test_preserves_atlas_metadata() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.B,
            96,
            96,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert mapping.tile_width == atlas.tile_width
    assert mapping.tile_height == atlas.tile_height
    assert mapping.width == atlas.width
    assert mapping.height == atlas.height


def test_maps_tiles_from_multiple_sheets() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.A5, 96, 96),
        make_sheet(SheetType.B, 96, 96),
        make_sheet(SheetType.C, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    refs_by_sheet = {
        sheet_type: [
            tile
            for tile in mapping.tiles
            if tile.ref.sheet_type == sheet_type
        ]
        for sheet_type in (
            SheetType.A5,
            SheetType.B,
            SheetType.C,
        )
    }

    assert len(refs_by_sheet[SheetType.A5]) == 4
    assert len(refs_by_sheet[SheetType.B]) == 4
    assert len(refs_by_sheet[SheetType.C]) == 4


def test_mapping_is_deterministic() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.C, 96, 96),
        make_sheet(SheetType.A5, 96, 96),
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)

    mapper = GodotAtlasMapper()

    first = mapper.map(atlas)
    second = mapper.map(atlas)

    assert first == second


def test_preserves_atlas_dimensions() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert mapping.width == atlas.width
    assert mapping.height == atlas.height
    assert mapping.tile_width == atlas.tile_width
    assert mapping.tile_height == atlas.tile_height


def test_preserves_tile_dimensions() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert [
        (tile.width, tile.height)
        for tile in mapping.tiles
    ] == [
        (placement.width, placement.height)
        for placement in atlas.placements
    ]


def test_preserves_sheet_mapping() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.C, 96, 96),
        make_sheet(SheetType.A5, 96, 96),
        make_sheet(SheetType.B, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert [
        tile.ref.sheet_type
        for tile in mapping.tiles
    ] == [
        SheetType.A5,
        SheetType.A5,
        SheetType.A5,
        SheetType.A5,
        SheetType.B,
        SheetType.B,
        SheetType.B,
        SheetType.B,
        SheetType.C,
        SheetType.C,
        SheetType.C,
        SheetType.C,
    ]


def test_preserves_vertical_sheet_offsets() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.A5, 96, 96),
        make_sheet(SheetType.B, 96, 96),
        make_sheet(SheetType.C, 96, 96),
    )

    atlas = AtlasBuilder().build(tileset)

    mapping = GodotAtlasMapper().map(atlas)

    assert [
        (
            tile.ref.sheet_type,
            tile.atlas_x,
            tile.atlas_y,
        )
        for tile in mapping.tiles
        if tile.ref.index == 0
    ] == [
        (SheetType.A5, 0, 0),
        (SheetType.B, 0, 96),
        (SheetType.C, 0, 192),
    ]