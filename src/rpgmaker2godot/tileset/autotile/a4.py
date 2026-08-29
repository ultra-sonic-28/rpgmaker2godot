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

from collections.abc import Callable, Hashable, Iterator

from PIL import Image

from .composer import QUARTER_SIZE, compose_autotile
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
# width of the other sheets). The number of rows follows the number of
# *graphically distinct* tiles (see a4_unique_tiles), not the raw
# 2304 engine IDs nor the 1536 distinct compositions.
A4_PACK_COLUMNS = 16
A4_PACK_WIDTH = A4_PACK_COLUMNS * 48


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


def a4_unique_compositions() -> Iterator[
    tuple[int, tuple[tuple[int, int, int, int], ...]]
]:
    """Yield ``(index, quarters)`` for each **distinct** A4 composition.

    RPG Maker reserves 48 shape IDs per autotile kind, but the Wall
    Side table only holds 16 shapes (cycled with ``shape % 16``): 32 of
    the 48 unfolded variants of every Wall Side compose the exact same
    tile. This generator walks the (kind, shape) pairs in engine ID
    order and yields only the first occurrence of each distinct
    quarter composition:

    * 24 Wall Tops x 48 distinct shapes;
    * 24 Wall Sides x 16 distinct shapes;

    i.e. the 48 x 48 = 2304 raw variants reduce to 1536 unique 48x48
    tiles. ``index`` is the RPG Maker A4 offset (``local_kind * 48 +
    shape``) of the first occurrence and ``quarters`` the
    ``a4_shape_quarters`` tuple identifying the composed tile
    (absolute source coordinates, draw order).
    """

    seen: set[tuple[tuple[int, int, int, int], ...]] = set()

    for local_kind in range(A4_AUTOTILE_COUNT):
        for shape in range(A4_SHAPES_PER_AUTOTILE):
            quarters = a4_shape_quarters(local_kind, shape)

            if quarters in seen:
                continue

            seen.add(quarters)

            yield local_kind * A4_SHAPES_PER_AUTOTILE + shape, quarters


def a4_unique_tiles(
    source: Image.Image,
    *,
    dedup_key: Callable[[int, bytes], Hashable] | None = None,
) -> Iterator[tuple[int, tuple[tuple[int, int, int, int], ...]]]:
    """Yield ``(index, quarters)`` for each **graphically distinct** tile.

    Walks :func:`a4_unique_compositions` in engine ID order, composes
    every candidate into its final 48x48 image and keeps only the first
    occurrence of each distinct pixel content (exact, byte-for-byte
    comparison of the composed RGBA pixels). Two different compositions
    can still render identically when the source quarters they select
    are visually the same — uniform fills are common in stock A4
    sheets: for the stock ``Inside_A4.png`` this pass shrinks the 1536
    distinct compositions down to 1390 distinct tiles.

    Args:
        source: The RGBA ``*_A4.png`` sheet image (768x720).
        dedup_key: Optional hook returning the identity used to detect
            duplicates. It receives ``(index, pixel_signature)`` where
            ``pixel_signature`` is the raw RGBA byte content of the
            composed tile. Defaults to the pixel signature itself. The
            converter passes a hook that also discriminates on the
            resolved collision so that graphically identical tiles with
            *different* passage flags stay separate.

    Yields:
        ``(index, quarters)`` pairs where ``index`` is the RPG Maker A4
        offset (``local_kind * 48 + shape``) of the first occurrence and
        ``quarters`` the :func:`a4_shape_quarters` tuple identifying the
        composed tile (absolute source coordinates, draw order).
    """

    seen: set[Hashable] = set()

    for index, quarters in a4_unique_compositions():
        local_kind, shape = divmod(index, A4_SHAPES_PER_AUTOTILE)

        source_x, source_y, is_wall_side = a4_source_region(local_kind)

        table = WALL_AUTOTILE_TABLE if is_wall_side else FLOOR_AUTOTILE_TABLE

        tile = compose_autotile(
            source,
            source_x=source_x,
            source_y=source_y,
            shape=table[shape % len(table)],
        )

        signature = tile.tobytes()
        tile.close()

        key = (
            dedup_key(index, signature)
            if dedup_key is not None
            else signature
        )

        if key in seen:
            continue

        seen.add(key)

        yield index, quarters


# Number of distinct A4 quarter compositions: the 2304 raw engine IDs
# minus the Wall Side shape repetitions (48 IDs per kind but only 16
# distinct shapes). Graphically identical tiles are merged later by
# a4_unique_tiles, so the packed tile count of a converted sheet is
# image-dependent and always <= this value.
A4_UNIQUE_COMPOSITION_COUNT = sum(1 for _ in a4_unique_compositions())


__all__ = [
    "A4_AUTOTILE_COUNT",
    "A4_COLUMNS",
    "A4_HEIGHT",
    "A4_PACK_COLUMNS",
    "A4_PACK_WIDTH",
    "A4_SHAPES_PER_AUTOTILE",
    "A4_SLOT_HEIGHT",
    "A4_SLOT_WIDTH",
    "A4_UNIQUE_COMPOSITION_COUNT",
    "A4_WIDTH",
    "a4_shape_quarters",
    "a4_source_region",
    "a4_unique_compositions",
    "a4_unique_tiles",
]