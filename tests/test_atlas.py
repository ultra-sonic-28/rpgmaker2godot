from pathlib import Path
import pytest

from rpgmaker2godot.atlas import AtlasBuilder
from rpgmaker2godot.model import Sheet, SheetType, Tile, TileRef, Tileset

from tests.helpers.atlas import (
    make_sheet,
    make_tileset,
    make_tileset_with_sheets,
)


def test_builds_atlas_dimensions() -> None:
    atlas = AtlasBuilder().build(make_tileset())

    assert atlas.width == 96
    assert atlas.height == 96
    assert atlas.tile_width == 48
    assert atlas.tile_height == 48


def test_builds_explicit_tile_mapping() -> None:
    atlas = AtlasBuilder().build(make_tileset())

    assert len(atlas.placements) == 4

    placement_0 = atlas.placements[0]
    placement_1 = atlas.placements[1]
    placement_2 = atlas.placements[2]
    placement_3 = atlas.placements[3]

    assert placement_0.tile == TileRef(
        tileset="Inside",
        sheet_type=SheetType.B,
        index=0,
    )
    assert placement_0.source_path == Path("Inside_B.png")
    assert (placement_0.atlas_x, placement_0.atlas_y) == (0, 0)
    assert (placement_0.width, placement_0.height) == (48, 48)

    assert placement_1.tile == TileRef(
        tileset="Inside",
        sheet_type=SheetType.B,
        index=1,
    )
    assert placement_1.source_path == Path("Inside_B.png")
    assert (placement_1.atlas_x, placement_1.atlas_y) == (48, 0)
    assert (placement_1.width, placement_1.height) == (48, 48)

    assert placement_2.tile == TileRef(
        tileset="Inside",
        sheet_type=SheetType.B,
        index=2,
    )
    assert placement_2.source_path == Path("Inside_B.png")
    assert (placement_2.atlas_x, placement_2.atlas_y) == (0, 48)
    assert (placement_2.width, placement_2.height) == (48, 48)

    assert placement_3.tile == TileRef(
        tileset="Inside",
        sheet_type=SheetType.B,
        index=3,
    )
    assert placement_3.source_path == Path("Inside_B.png")
    assert (placement_3.atlas_x, placement_3.atlas_y) == (48, 48)
    assert (placement_3.width, placement_3.height) == (48, 48)


def test_builds_atlas_from_multiple_sheets() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            width=384,
            height=768,
        ),
        make_sheet(
            SheetType.B,
            width=768,
            height=768,
        ),
        make_sheet(
            SheetType.C,
            width=768,
            height=768,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    assert atlas.width == 768
    assert atlas.height == 2304


def test_places_sheets_vertically() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            width=384,
            height=768,
        ),
        make_sheet(
            SheetType.B,
            width=768,
            height=768,
        ),
        make_sheet(
            SheetType.C,
            width=768,
            height=768,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    a5 = next(
        placement
        for placement in atlas.placements
        if placement.tile.sheet_type == SheetType.A5
    )

    b = next(
        placement
        for placement in atlas.placements
        if placement.tile.sheet_type == SheetType.B
    )

    c = next(
        placement
        for placement in atlas.placements
        if placement.tile.sheet_type == SheetType.C
    )

    assert a5.atlas_y == 0
    assert b.atlas_y == 768
    assert c.atlas_y == 1536


def test_preserves_source_coordinates() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            width=384,
            height=768,
        ),
        make_sheet(
            SheetType.B,
            width=768,
            height=768,
        ),
    )

    atlas = AtlasBuilder().build(tileset)

    placement = next(
        placement
        for placement in atlas.placements
        if (
            placement.tile.sheet_type == SheetType.B
            and placement.tile.index == 17
        )
    )

    assert placement.source_x == 48
    assert placement.source_y == 48

    assert placement.atlas_x == 48
    assert placement.atlas_y == 768 + 48


def test_rejects_inconsistent_tile_sizes() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(
            SheetType.A5,
            width=384,
            height=768,
            tile_width=48,
            tile_height=48,
        ),
        make_sheet(
            SheetType.B,
            width=768,
            height=768,
            tile_width=32,
            tile_height=32,
        ),
    )

    with pytest.raises(
        ValueError,
        match="same tile size",
    ):
        AtlasBuilder().build(tileset)


def test_sheets_are_ordered() -> None:
    tileset = make_tileset_with_sheets(
        make_sheet(SheetType.C, 768, 768),
        make_sheet(SheetType.A5, 384, 768),
        make_sheet(SheetType.B, 768, 768),
    )

    atlas = AtlasBuilder().build(tileset)

    placements = [
        placement
        for placement in atlas.placements
        if placement.tile.index == 0
    ]

    assert [
        placement.tile.sheet_type
        for placement in placements
    ] == [
        SheetType.A5,
        SheetType.B,
        SheetType.C,
    ]