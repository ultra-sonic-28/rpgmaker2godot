from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.model.tile import Tile
from rpgmaker2godot.tileset.tile_id import SHEET_TILE_ID_BASE, tile_to_tile_id
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


def test_a4_tile_id() -> None:
    """A4 Tile IDs are base + index (index = local_kind*48 + shape)."""

    tile = Tile(
        ref=make_tile_ref(
            index=3,
            sheet_type=SheetType.A4,
        ),
        column=0,
        row=0,
        x=0,
        y=0,
        width=48,
        height=48,
    )

    assert tile_to_tile_id(tile) == 5888 + 3


def test_a4_flag_block_base() -> None:
    """A4 sits at global Tile ID 5888 (TILE_ID_A4 of rmmz_core.js).

    The previous value (3328) was wrong: the A-series autotile regions
    are A1=2048, A2=2816, A3=4352, A4=5888. The converter stores
    ``index = local_kind * 48 + shape`` so the ID is simply base +
    index, which stays inside the 8192-entry flags arrays.
    """

    assert SHEET_TILE_ID_BASE[SheetType.A4] == 5888
    assert SHEET_TILE_ID_BASE[SheetType.A5] == 1536