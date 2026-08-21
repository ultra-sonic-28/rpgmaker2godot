from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.model.tile import Tile
from rpgmaker2godot.tileset.tile_id import tile_to_tile_id
from tests.helpers.atlas import make_tile_ref


def test_b_tile_id() -> None:
    tile = Tile(
        ref=make_tile_ref(
            index=0,
            sheet_type=SheetType.B,
        ),
        column=5,
        row=2,
        x=5 * 48,
        y=2 * 48,
        width=48,
        height=48,
    )

    assert tile_to_tile_id(tile) == 37


def test_a5_tile_id() -> None:
    tile = Tile(
        ref=make_tile_ref(
            index=0,
            sheet_type=SheetType.A5,
        ),
        column=3,
        row=4,
        x=3 * 48,
        y=4 * 48,
        width=48,
        height=48,
    )

    assert tile_to_tile_id(tile) == 1536 + 4 * 8 + 3