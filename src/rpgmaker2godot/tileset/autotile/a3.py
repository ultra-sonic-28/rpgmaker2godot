"""Map the 32 A3 building autotiles to their source regions and tables.

RPG Maker MZ stores the A3 sheet (``*_A3.png``, 768x384) as a grid of
**autotile sources**. Each source is a multi-quarter region which, in
the game, is composed at draw time into the connection variants using a
shape table.

This module mirrors the authoritative decode in ``rmmz_core.js``
(``Tilemap.prototype._addAutotile``, the ``isTileA3`` branch):

* ``local_kind`` spans 0..31 = one A3 autotile per slot:
  ``8`` columns ``x`` 4 vertical slots.
* ``tx = local_kind % 8`` (which 96px-wide column) and
  ``ty = 6 + local_kind // 8`` select the source region (the engine
  reads quarters at ``((tx * 4 + qsx) * 24, ((ty - 6) * 4 + qsy) * 24)``
  px, i.e. one 96px step per slot on both axes).
* every A3 autotile composes from the **Wall** source
  (WALL_AUTOTILE_TABLE, 16 shapes): rows whose ``kind % 16 < 8`` are
  Roof autotiles (``Tilemap.isRoofTile``), the others Wall autotiles
  (``Tilemap.isWallSideTile``), but both use the same 16-shape table.

Each source occupies a 96x96 region (four quarter rows), stacked per
column (384px tall in total).
"""

from collections.abc import Callable, Hashable, Iterator

from PIL import Image

from .composer import QUARTER_SIZE
from .shapes import WALL_AUTOTILE_TABLE
from .unique import Quarters, unique_tiles

# One autotile occupies a 96px source slot, exactly two tiles wide and
# two tiles tall.
A3_SLOT_WIDTH = 96
A3_SLOT_HEIGHT = 96

# Left edge of a source column / top edge of a source row.
A3_COLUMNS = 8
A3_ROWS = 4

# Number of autotiles in one A3 sheet (local kind 0..31).
A3_AUTOTILE_COUNT = 32

# Canonical outer dimensions of the A3 sheet.
A3_WIDTH = 768
A3_HEIGHT = 384

# RPG Maker reserves exactly 48 Tile IDs per autotile kind: the shape
# index runs 0..47 even though the Wall table only has 16 shapes
# (they are cycled with ``shape % 16``).
A3_SHAPES_PER_AUTOTILE = 48

# Packing of the unfolded A3 tiles inside their atlas region: a 16 tile
# per row grid, so each row is 16 * 48 = 768 px wide (matching the
# width of the other sheets). The number of rows follows the number of
# *graphically distinct* tiles (see a3_unique_tiles), not the raw
# 1536 engine IDs nor the 512 distinct compositions.
A3_PACK_COLUMNS = 16
A3_PACK_WIDTH = A3_PACK_COLUMNS * 48


def a3_source_region(
    local_kind: int,
) -> tuple[int, int]:
    """Return ``(source_x, source_y)`` for one A3 autotile.

    ``source_x``/``source_y`` are the pixel top-left of the autotile
    source region in the ``*_A3.png`` (768x384) sheet. Every A3
    autotile — Roof or Wall — occupies a 96x96 region: four quarter
    rows of the shared WALL_AUTOTILE_TABLE.

    The mapping is computed from the authoritative ``rmmz_core.js``
    formula (``bx = tx * 2``, ``by = (ty - 6) * 2`` with
    ``ty = 6 + local_kind // 8``) so it stays correct without guessing.
    """

    if not 0 <= local_kind < A3_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A3_AUTOTILE_COUNT}), got {local_kind}."
        )

    tx = local_kind % 8
    ty = 6 + local_kind // 8

    source_x = tx * A3_SLOT_WIDTH
    source_y = (ty - 6) * A3_SLOT_HEIGHT

    return source_x, source_y


def a3_shape_quarters(
    local_kind: int,
    shape: int,
) -> Quarters:
    """Return the four ``(qx, qy, dx, dy)`` pieces of one unfolded tile.

    ``(qx, qy)`` are the source offsets (px, relative to the autotile
    region origin) of the 24x24 quarter, in (top-left, top-right,
    bottom-left, bottom-right) draw order. ``(dx, dy)`` is the position
    of that quarter inside the resulting 48x48 tile.

    ``shape`` runs 0..47 and selects the engine shape table entry
    (``shape % len(table)``), matching RPG Maker's per-kind Tile ID
    layout.
    """

    source_x, source_y = a3_source_region(local_kind)

    entry = WALL_AUTOTILE_TABLE[shape % len(WALL_AUTOTILE_TABLE)]

    return tuple(
        (
            source_x + quarter_x * QUARTER_SIZE,
            source_y + quarter_y * QUARTER_SIZE,
            (index % 2) * QUARTER_SIZE,
            (index // 2) * QUARTER_SIZE,
        )
        for index, (quarter_x, quarter_y) in enumerate(entry)
    )


def a3_unique_compositions() -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for each **distinct** A3 composition.

    RPG Maker reserves 48 shape IDs per autotile kind, but the Wall
    table only holds 16 shapes (cycled with ``shape % 16``): 32 of
    the 48 unfolded variants of every kind compose the exact same
    tile. This generator walks the (kind, shape) pairs in engine ID
    order and yields only the first occurrence of each distinct
    quarter composition, i.e. the 32 x 48 = 1536 raw variants reduce
    to 512 unique 48x48 tiles (32 kinds x 16 shapes). ``index`` is the
    RPG Maker A3 offset (``local_kind * 48 + shape``) of the first
    occurrence and ``quarters`` the ``a3_shape_quarters`` tuple
    identifying the composed tile (absolute source coordinates, draw
    order).
    """

    seen: set[Quarters] = set()

    for local_kind in range(A3_AUTOTILE_COUNT):
        for shape in range(A3_SHAPES_PER_AUTOTILE):
            quarters = a3_shape_quarters(local_kind, shape)

            if quarters in seen:
                continue

            seen.add(quarters)

            yield local_kind * A3_SHAPES_PER_AUTOTILE + shape, quarters


def a3_unique_tiles(
    source: Image.Image,
    *,
    tolerance: int = 0,
    dedup_key: Callable[[int, bytes], Hashable] | None = None,
) -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for each **graphically distinct** tile.

    Walks :func:`a3_unique_compositions` in engine ID order, composes
    every candidate into its final 48x48 image and keeps only the first
    occurrence of each distinct pixel content (exact, byte-for-byte
    comparison of the composed RGBA pixels). Two different compositions
    can still render identically when the source quarters they select
    are visually the same — uniform fills are common in stock A3
    sheets.

    With ``tolerance > 0``, two tiles are also considered identical
    when they differ by at most ``tolerance`` **pixels** (in any RGBA
    channel), discarding noise inherited from the source sheet. The
    first occurrence is still the tile kept. ``tolerance = 0`` (the
    default) requires byte-exact pixels.

    Args:
        source: The RGBA ``*_A3.png`` sheet image (768x384).
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

    Yields:
        ``(index, quarters)`` pairs where ``index`` is the RPG Maker A3
        offset (``local_kind * 48 + shape``) of the first occurrence and
        ``quarters`` the :func:`a3_shape_quarters` tuple identifying the
        composed tile (absolute source coordinates, draw order).
    """

    return unique_tiles(
        a3_unique_compositions(),
        source,
        tolerance=tolerance,
        dedup_key=dedup_key,
    )


# Number of distinct A3 quarter compositions: the 1536 raw engine IDs
# cycle the 16-shape Wall table (48 IDs per kind but only 16 distinct
# shapes). Graphically identical tiles are merged later by
# a3_unique_tiles, so the packed tile count of a converted sheet is
# image-dependent and always <= this value.
A3_UNIQUE_COMPOSITION_COUNT = sum(1 for _ in a3_unique_compositions())


__all__ = [
    "A3_AUTOTILE_COUNT",
    "A3_COLUMNS",
    "A3_HEIGHT",
    "A3_PACK_COLUMNS",
    "A3_PACK_WIDTH",
    "A3_ROWS",
    "A3_SHAPES_PER_AUTOTILE",
    "A3_SLOT_HEIGHT",
    "A3_SLOT_WIDTH",
    "A3_UNIQUE_COMPOSITION_COUNT",
    "A3_WIDTH",
    "a3_shape_quarters",
    "a3_source_region",
    "a3_unique_compositions",
    "a3_unique_tiles",
]