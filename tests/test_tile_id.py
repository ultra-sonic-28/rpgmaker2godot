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


def test_a3_tile_id() -> None:
    """A3 Tile IDs are base + index (index = local_kind*48 + shape)."""

    tile = Tile(
        ref=make_tile_ref(
            index=49,  # kind 1, shape 1.
            sheet_type=SheetType.A3,
        ),
        column=0,
        row=0,
        x=0,
        y=0,
        width=48,
        height=48,
    )

    assert tile_to_tile_id(tile) == 4352 + 49


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


def test_a2_tile_id() -> None:
    """A2 Tile IDs are base + index (index = local_kind*48 + shape)."""

    tile = Tile(
        ref=make_tile_ref(
            index=49,  # kind 1, shape 1.
            sheet_type=SheetType.A2,
        ),
        column=0,
        row=0,
        x=0,
        y=0,
        width=48,
        height=48,
    )

    assert tile_to_tile_id(tile) == 2816 + 49


def test_a2_a3_and_a4_flag_block_base() -> None:
    """A2 sits at global Tile ID 2816, A3 at 4352 and A4 at 5888.

    The A-series autotile regions are A1=2048, A2=2816, A3=4352,
    A4=5888 (rmmz_core.js). The converter stores
    ``index = local_kind * 48 + shape`` so the ID is simply
    base + index, which stays inside the 8192-entry flags arrays.
    """

    assert SHEET_TILE_ID_BASE[SheetType.A2] == 2816
    assert SHEET_TILE_ID_BASE[SheetType.A3] == 4352
    assert SHEET_TILE_ID_BASE[SheetType.A4] == 5888
    assert SHEET_TILE_ID_BASE[SheetType.A5] == 1536