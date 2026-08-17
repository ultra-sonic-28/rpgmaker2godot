from pathlib import Path

from rpgmaker2godot.atlas import AtlasBuilder
from rpgmaker2godot.model import Sheet, SheetType, Tile, TileRef


def make_sheet() -> Sheet:
    tiles = tuple(
        Tile(
            ref=TileRef(
                tileset="Inside",
                sheet_type=SheetType.B,
                index=index,
            ),
            column=index % 2,
            row=index // 2,
            x=(index % 2) * 48,
            y=(index // 2) * 48,
            width=48,
            height=48,
        )
        for index in range(4)
    )

    return Sheet(
        sheet_type=SheetType.B,
        source_path=Path("Inside_B.png"),
        width=96,
        height=96,
        tile_width=48,
        tile_height=48,
        columns=2,
        rows=2,
        tiles=tiles,
    )


def test_builds_atlas_dimensions() -> None:
    atlas = AtlasBuilder().build(make_sheet())

    assert atlas.width == 96
    assert atlas.height == 96
    assert atlas.tile_width == 48
    assert atlas.tile_height == 48


def test_builds_explicit_tile_mapping() -> None:
    atlas = AtlasBuilder().build(make_sheet())

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