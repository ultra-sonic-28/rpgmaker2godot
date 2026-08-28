"""Map the 48 A4 wall autotiles to their source regions and tables.

RPG Maker MZ stores the A4 sheet (``*_A4.png``, 768x720) as a grid of
**autotile sources**. Each source is a multi-quarter region which, in
the game, is composed at draw time into the connection variants using a
shape table.

This module mirrors the authoritative decode in ``rmmz_core.js``
(``Tilemap.prototype._addAutotile``, the ``isTileA4`` branch):

* ``local_kind`` spans 0..47 = one A4 autotile per column slot:
  ``8`` columns ``x`` 6 vertical slots.
* ``tx = local_kind % 8`` (which 96px-wide column) and
  ``ty = 10 + local_kind // 8`` select the source region.
* ``ty % 2 == 1`` selects the **Wall Side** source (WALL_AUTOTILE_TABLE,
  16 shapes); ``ty % 2 == 0`` selects the **Wall Top** source
  (FLOOR_AUTOTILE_TABLE, 48 shapes).

The Wall Side source occupies a 96x96 region and the Wall Top source a
96x144 region, stacked per column (720px tall in total).
"""

from .composer import QUARTER_SIZE
from .shapes import FLOOR_AUTOTILE_TABLE, WALL_AUTOTILE_TABLE

# One autotile occupies a 96px-wide source slot, exactly two tiles wide.
A4_SLOT_WIDTH = 96

# Left edge of a source column.
A4_COLUMNS = 8
A4_SLOT_HEIGHT = 48  # one vertical source step, in pixels units.

# Number of autotiles in one A4 sheet (local kind 0..47).
A4_AUTOTILE_COUNT = 48

# Canonical outer dimensions of the A4 sheet.
A4_WIDTH = 768
A4_HEIGHT = 720

# RPG Maker reserves exactly 48 Tile IDs per autotile kind: the shape
# index runs 0..47 even though the Wall Side table only has 16 shapes
# (they are cycled with ``shape % 16``).
A4_SHAPES_PER_AUTOTILE = 48

# Packing of the unfolded A4 tiles inside their atlas region: a 16 tile
# per row grid, so each row is 16 * 48 = 768 px wide (matching the
# width of the other sheets). 48 autotiles * 48 shapes = 2304 tiles,
# packed as 144 rows.
A4_PACK_COLUMNS = 16
A4_PACK_WIDTH = A4_PACK_COLUMNS * 48
A4_PACK_ROWS = (A4_AUTOTILE_COUNT * A4_SHAPES_PER_AUTOTILE) // A4_PACK_COLUMNS
A4_PACK_HEIGHT = A4_PACK_ROWS * 48


def a4_source_region(
    local_kind: int,
) -> tuple[int, int, bool]:
    """Return ``(source_x, source_y, is_wall_side)`` for one A4 autotile.

    ``source_x``/``source_y`` are the pixel top-left of the autotile
    source region in the ``*_A4.png`` (768x720) sheet:

    * ``is_wall_side == False`` -> Wall Top, region is A4_SLOT_WIDTH x
      144 (6 quarter rows, FLOOR_AUTOTILE_TABLE).
    * ``is_wall_side == True`` -> Wall Side, region is A4_SLOT_WIDTH x
      96 (4 quarter rows, WALL_AUTOTILE_TABLE).

    The mapping is computed from the authoritative ``rmmz_core.js``
    formula so it stays correct without guessing.
    """

    if not 0 <= local_kind < A4_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A4_AUTOTILE_COUNT}), got {local_kind}."
        )

    tx = local_kind % 8
    ty = 10 + local_kind // 8

    # by = floor((ty - 10) * 2.5 + (ty % 2 == 1 ? 0.5 : 0))
    by = (ty - 10) * 2.5 + (0.5 if ty % 2 == 1 else 0.0)
    by = int(by)  # by is an integer for ty in [10, 15]

    source_x = tx * A4_SLOT_WIDTH
    source_y = by * A4_SLOT_HEIGHT

    return source_x, source_y, ty % 2 == 1


def a4_shape_quarters(
    local_kind: int,
    shape: int,
) -> tuple[tuple[int, int, int, int], ...]:
    """Return the four ``(qx, qy, dx, dy)`` pieces of one unfolded tile.

    ``(qx, qy)`` are the source offsets (px, relative to the autotile
    region origin) of the 24x24 quarter, in (top-left, top-right,
    bottom-left, bottom-right) draw order. ``(dx, dy)`` is the position
    of that quarter inside the resulting 48x48 tile.

    ``shape`` runs 0..47 and selects the engine shape table entry
    (``shape % len(table)``), matching RPG Maker's per-kind Tile ID
    layout.
    """

    source_x, source_y, is_wall_side = a4_source_region(local_kind)

    table = WALL_AUTOTILE_TABLE if is_wall_side else FLOOR_AUTOTILE_TABLE
    entry = table[shape % len(table)]

    return tuple(
        (
            source_x + quarter_x * QUARTER_SIZE,
            source_y + quarter_y * QUARTER_SIZE,
            (index % 2) * QUARTER_SIZE,
            (index // 2) * QUARTER_SIZE,
        )
        for index, (quarter_x, quarter_y) in enumerate(entry)
    )


__all__ = [
    "A4_AUTOTILE_COUNT",
    "A4_COLUMNS",
    "A4_HEIGHT",
    "A4_PACK_COLUMNS",
    "A4_PACK_HEIGHT",
    "A4_PACK_ROWS",
    "A4_PACK_WIDTH",
    "A4_SHAPES_PER_AUTOTILE",
    "A4_SLOT_HEIGHT",
    "A4_SLOT_WIDTH",
    "A4_WIDTH",
    "a4_shape_quarters",
    "a4_source_region",
]