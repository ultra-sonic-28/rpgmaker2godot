from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.model.tile import Tile, TileRef

SHEET_TILE_ID_BASE: dict[SheetType, int] = {
    # RPG Maker stores B-E in consecutive blocks of 256 IDs.
    SheetType.B: 0,
    SheetType.C: 256,
    SheetType.D: 512,
    SheetType.E: 768,

    # A5 (flat ground) starts at Tile ID 1536.
    SheetType.A5: 1536,

    # The A-series autotile regions follow rmmz_core.js:
    #   A1 = 2048, A2 = 2816, A3 = 4352, A4 = 5888, MAX = 8192.
    # A4 contains 48 autotiles x 48 shapes = 2304 Tile IDs. Our
    # converter stores ``index = local_kind * 48 + shape`` on the TileRef
    # so the Tile ID is simply ``base + index``.
    SheetType.A4: 5888,
}


SHEET_COLUMNS: dict[SheetType, int] = {
    # B-E are 16 columns wide.
    SheetType.B: 16,
    SheetType.C: 16,
    SheetType.D: 16,
    SheetType.E: 16,

    # A5 is 8 columns wide; the 16-column entry below is A4 only.
    SheetType.A5: 8,

    # A4 reads as a flat 16-column grid in the fallback pipeline path
    # (its native layout covers the two side-by-side wall autotiles).
    # The true autotile interpretation is handled by the autotile
    # expander.
    SheetType.A4: 16,
}


SHEET_ROWS: dict[SheetType, int] = {
    SheetType.B: 16,
    SheetType.C: 16,
    SheetType.D: 16,
    SheetType.E: 16,
    SheetType.A5: 16,
    SheetType.A4: 15,
}


def tile_ref_to_tile_id(tile: TileRef) -> int:
    """Convert a RPG Maker sheet position into its global Tile ID.

    RPG Maker does not store passability flags by sheet and cell.
    Instead, Tilesets.json stores one flat `flags` array indexed by
    the global Tile ID.

    This function bridges our internal representation (`TileRef`)
    and RPG Maker's representation.
    """

    if tile.sheet_type == SheetType.A4:
        # A4 is unfolded per autotile: index = local_kind * 48 + shape,
        # ID = base + index (base = TILE_ID_A4 = 5888).
        return SHEET_TILE_ID_BASE[SheetType.A4] + tile.index

    try:
        base = SHEET_TILE_ID_BASE[tile.sheet_type]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported sheet type: {tile.sheet_type!r}"
        ) from exc

    try:
        columns = SHEET_COLUMNS[tile.sheet_type]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported sheet type: {tile.sheet_type!r}"
        ) from exc

    if tile.column < 0:
        raise ValueError(
            f"Tile column must be >= 0, got {tile.column}."
        )

    if tile.row < 0:
        raise ValueError(
            f"Tile row must be >= 0, got {tile.row}."
        )

    if tile.column >= columns:
        raise ValueError(
            f"Tile column {tile.column} is outside "
            f"{tile.sheet_type.name} ({columns} columns)."
        )

    return base + tile.row * columns + tile.column


def tile_to_tile_id(tile: Tile) -> int:
    """Return the RPG Maker global Tile ID for a tile.

    RPG Maker does not index the `flags` array by our internal
    `Tile.index`. The flags array is indexed by the global Tile ID.

    For the non-autotile sheets currently supported by the converter:

        B = 0
        C = 256
        D = 512
        E = 768
        A5 = 1536

    The position inside a sheet is then calculated from its
    column and row.
    """

    sheet_type = tile.ref.sheet_type

    if sheet_type == SheetType.A4:
        # A4 is unfolded per autotile: index = local_kind * 48 + shape,
        # ID = base + index (base = TILE_ID_A4 = 5888).
        return SHEET_TILE_ID_BASE[SheetType.A4] + tile.ref.index

    try:
        base = SHEET_TILE_ID_BASE[sheet_type]
        columns = SHEET_COLUMNS[sheet_type]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported RPG Maker sheet type: {sheet_type!r}"
        ) from exc

    if tile.column < 0:
        raise ValueError(
            f"Tile column must be >= 0, got {tile.column}."
        )

    if tile.row < 0:
        raise ValueError(
            f"Tile row must be >= 0, got {tile.row}."
        )

    if tile.column >= columns:
        raise ValueError(
            f"Tile column {tile.column} is outside "
            f"{sheet_type.name} ({columns} columns)."
        )

    return base + tile.row * columns + tile.column