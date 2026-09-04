"""Map the 32 A2 ground autotiles to their source regions and tables.

RPG Maker MZ stores the A2 sheet (``*_A2.png``, 768x576) as a grid of
**autotile sources**. Each source is a multi-quarter region which, in
the game, is composed at draw time into the connection variants using a
shape table.

This module mirrors the authoritative decode in ``rmmz_core.js``
(``Tilemap.prototype._addAutotile``, the ``isTileA2`` branch):

* ``local_kind`` spans 0..31 = one A2 autotile per slot: ``8`` columns
  ``x`` 4 vertical slots (the engine numbers them 16..47, hence its
  ``ty = 2 + local_kind // 8`` and ``by = (ty - 2) * 3``).
* ``tx = local_kind % 8`` (which 96px-wide column) and
  ``ty = local_kind // 8`` select the source region (the engine reads
  quarters at ``((tx * 4 + qsx) * 24, (ty * 6 + qsy) * 24)`` px, i.e.
  one 96x144 step per slot on both axes).
* every A2 autotile composes from the full **Floor** source
  (FLOOR_AUTOTILE_TABLE, 48 shapes) — the classic blob autotile.
* ``Tilemap._isTableTile`` (flag ``0x80``, the "counter" property)
  enables the *table* rendering: source quarters at rows 1 or 5 are
  replaced by the matching row-3 quarter whose bottom half is redrawn
  from the top half of the original quarter (see
  :func:`a2_shape_quarters`). RPG Maker stores one flag per autotile
  kind, so table-ness is decided per kind, not per shape.

Each source occupies a 96x144 region (six quarter rows), stacked per
column (576px tall in total).
"""

from collections.abc import Callable, Collection, Hashable, Iterator

from PIL import Image

from .composer import QUARTER_SIZE, QuarterPiece
from .shapes import FLOOR_AUTOTILE_TABLE
from .unique import Quarters, unique_tiles

# One autotile occupies a 96x144 source slot: two tiles wide, three
# tiles tall (six quarter rows).
A2_SLOT_WIDTH = 96
A2_SLOT_HEIGHT = 144

# Left edge of a source column / top edge of a source row.
A2_COLUMNS = 8
A2_ROWS = 4

# Number of autotiles in one A2 sheet (local kind 0..31).
A2_AUTOTILE_COUNT = 32

# Canonical outer dimensions of the A2 sheet.
A2_WIDTH = 768
A2_HEIGHT = 576

# RPG Maker reserves exactly 48 Tile IDs per autotile kind and the
# Floor table holds exactly 48 shapes: every shape ID is a distinct
# quarter composition (no shape cycling, unlike the wall table).
A2_SHAPES_PER_AUTOTILE = 48

# Packing of the unfolded A2 tiles inside their atlas region: a 16 tile
# per row grid, so each row is 16 * 48 = 768 px wide (matching the
# width of the other sheets). The number of rows follows the number of
# *graphically distinct* tiles (see a2_unique_tiles), not the raw
# 1536 engine IDs.
A2_PACK_COLUMNS = 16
A2_PACK_WIDTH = A2_PACK_COLUMNS * 48

# Table rendering: quarters taken from these source quarter rows are
# replaced by the surface row (3), whose bottom half is redrawn from
# the top half of the original quarter (rmmz_core.js, ``isTable``
# branch of ``_addAutotile``).
_TABLE_QUARTER_ROWS = frozenset((1, 5))
_TABLE_SURFACE_ROW = 3
_QUARTER_COLUMNS = 4


def a2_source_region(
    local_kind: int,
) -> tuple[int, int]:
    """Return ``(source_x, source_y)`` for one A2 autotile.

    ``source_x``/``source_y`` are the pixel top-left of the autotile
    source region in the ``*_A2.png`` (768x576) sheet. Every A2
    autotile — grass, dirt, sand, snow, path… — occupies a 96x144
    region: six quarter rows of the shared FLOOR_AUTOTILE_TABLE.

    The mapping is computed from the authoritative ``rmmz_core.js``
    formula (``bx = tx * 2``, ``by = (ty - 2) * 3`` with
    ``ty = 2 + local_kind // 8``) so it stays correct without guessing.
    """

    if not 0 <= local_kind < A2_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A2_AUTOTILE_COUNT}), got {local_kind}."
        )

    tx = local_kind % 8
    ty = local_kind // 8

    source_x = tx * A2_SLOT_WIDTH
    source_y = ty * A2_SLOT_HEIGHT

    return source_x, source_y


def a2_shape_quarters(
    local_kind: int,
    shape: int,
    *,
    is_table: bool = False,
) -> Quarters:
    """Return the pieces of one unfolded A2 tile.

    Each piece is a ``(qx, qy, dx, dy, height)`` tuple: ``(qx, qy)``
    locates the 24px-wide piece in the sheet (absolute pixel
    coordinates, cropped from the *top* of that quarter row),
    ``(dx, dy)`` places it inside the resulting 48x48 tile and
    ``height`` is the piece height in pixels (a full quarter is 24,
    table halves are 12).

    ``shape`` runs 0..47 and selects the engine shape table entry
    (``FLOOR_AUTOTILE_TABLE[shape]``), matching RPG Maker's per-kind
    Tile ID layout.

    With ``is_table`` (the ``0x80`` counter flag), quarters whose
    source quarter row is 1 or 5 follow the engine's table rendering:
    the full mirrored row-3 quarter is drawn first, then the top half
    of the original quarter is drawn over its bottom half — hence two
    pieces for those quarters.
    """

    source_x, source_y = a2_source_region(local_kind)

    entry = FLOOR_AUTOTILE_TABLE[shape % len(FLOOR_AUTOTILE_TABLE)]

    pieces: list[QuarterPiece] = []

    for index, (quarter_x, quarter_y) in enumerate(entry):
        dest_x = (index % 2) * QUARTER_SIZE
        dest_y = (index // 2) * QUARTER_SIZE

        if is_table and quarter_y in _TABLE_QUARTER_ROWS:
            # qsx2 = (4 - qsx) % 4 mirrors row 1 quarters; row 5
            # quarters reuse their own column (rmmz_core.js).
            surface_x = (
                (_QUARTER_COLUMNS - quarter_x) % _QUARTER_COLUMNS
                if quarter_y == 1
                else quarter_x
            )

            pieces.append(
                (
                    source_x + surface_x * QUARTER_SIZE,
                    source_y + _TABLE_SURFACE_ROW * QUARTER_SIZE,
                    dest_x,
                    dest_y,
                    QUARTER_SIZE,
                )
            )

            pieces.append(
                (
                    source_x + quarter_x * QUARTER_SIZE,
                    source_y + quarter_y * QUARTER_SIZE,
                    dest_x,
                    dest_y + QUARTER_SIZE // 2,
                    QUARTER_SIZE // 2,
                )
            )
        else:
            pieces.append(
                (
                    source_x + quarter_x * QUARTER_SIZE,
                    source_y + quarter_y * QUARTER_SIZE,
                    dest_x,
                    dest_y,
                    QUARTER_SIZE,
                )
            )

    return tuple(pieces)


def a2_unique_compositions(
    table_kinds: Collection[int] = (),
) -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for every A2 composition.

    The A2 sheet reserves 48 shape IDs per kind and the Floor table
    holds exactly 48 shapes: all 32 x 48 = 1536 (kind, shape) pairs
    compose distinct quarter sets, so unlike the A3/A4 wall-table kinds
    nothing is skipped here. ``index`` is the RPG Maker A2 offset
    (``local_kind * 48 + shape``) and ``quarters`` the
    :func:`a2_shape_quarters` tuple identifying the composed tile
    (absolute source coordinates, draw order).

    ``table_kinds`` lists the autotile kinds rendered with the engine's
    table composition (the ``0x80`` counter flag); their shapes compose
    the table variant of the quarter set.
    """

    tables = frozenset(table_kinds)

    for local_kind in range(A2_AUTOTILE_COUNT):
        is_table = local_kind in tables

        for shape in range(A2_SHAPES_PER_AUTOTILE):
            yield (
                local_kind * A2_SHAPES_PER_AUTOTILE + shape,
                a2_shape_quarters(local_kind, shape, is_table=is_table),
            )


def a2_unique_tiles(
    source: Image.Image,
    *,
    tolerance: int = 0,
    dedup_key: Callable[[int, bytes], Hashable] | None = None,
    table_kinds: Collection[int] = (),
) -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for each **graphically distinct** tile.

    Walks :func:`a2_unique_compositions` in engine ID order, composes
    every candidate into its final 48x48 image and keeps only the first
    occurrence of each distinct pixel content (exact, byte-for-byte
    comparison of the composed RGBA pixels). Two different compositions
    can still render identically when the source quarters they select
    are visually the same — uniform fills are common in stock A2
    sheets.

    With ``tolerance > 0``, two tiles are also considered identical
    when they differ by at most ``tolerance`` **pixels** (in any RGBA
    channel), discarding noise inherited from the source sheet. The
    first occurrence is still the tile kept. ``tolerance = 0`` (the
    default) requires byte-exact pixels.

    Args:
        source: The RGBA ``*_A2.png`` sheet image (768x576).
        tolerance: Maximum number of differing pixels between two tiles
            for them to merge. ``0`` (default) means byte-exact
            comparison. Negative values are rejected.
        dedup_key: Optional hook returning an extra identity a duplicate
            must share. It receives ``(index, pixel_signature)`` where
            ``pixel_signature`` is the raw RGBA byte content of the
            composed tile; two tiles only merge when their keys are
            equal **and** their pixels match. Defaults to ``None`` (no
            extra constraint). The converter passes a hook returning the
            resolved collision so that graphically identical tiles with
            *different* passage flags stay separate.
        table_kinds: The autotile kinds rendered with the engine's
            table composition (the ``0x80`` counter flag, see
            :func:`a2_shape_quarters`).

    Yields:
        ``(index, quarters)`` pairs where ``index`` is the RPG Maker A2
        offset (``local_kind * 48 + shape``) of the first occurrence and
        ``quarters`` the :func:`a2_shape_quarters` tuple identifying the
        composed tile (absolute source coordinates, draw order).
    """

    if tolerance < 0:
        raise ValueError(
            f"tolerance must be >= 0, got {tolerance}."
        )

    return unique_tiles(
        a2_unique_compositions(table_kinds),
        source,
        tolerance=tolerance,
        dedup_key=dedup_key,
    )


# Number of distinct A2 quarter compositions: the 1536 raw engine IDs
# are all distinct (the Floor table holds exactly 48 shapes). Graphically
# identical tiles are merged later by a2_unique_tiles, so the packed
# tile count of a converted sheet is image-dependent and always <= this
# value.
A2_UNIQUE_COMPOSITION_COUNT = sum(1 for _ in a2_unique_compositions())


__all__ = [
    "A2_AUTOTILE_COUNT",
    "A2_COLUMNS",
    "A2_HEIGHT",
    "A2_PACK_COLUMNS",
    "A2_PACK_WIDTH",
    "A2_ROWS",
    "A2_SHAPES_PER_AUTOTILE",
    "A2_SLOT_HEIGHT",
    "A2_SLOT_WIDTH",
    "A2_UNIQUE_COMPOSITION_COUNT",
    "A2_WIDTH",
    "a2_shape_quarters",
    "a2_source_region",
    "a2_unique_compositions",
    "a2_unique_tiles",
]