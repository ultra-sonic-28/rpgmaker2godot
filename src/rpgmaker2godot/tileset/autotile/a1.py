"""Map the 16 A1 water autotiles to their source regions and tables.

RPG Maker MZ stores the A1 sheet (``*_A1.png``, 768x576) as a grid of
**autotile sources**. Each source is a multi-quarter region which, in
the game, is composed at draw time into the connection variants using a
shape table — and, uniquely for A1, into **animation frames**.

This module mirrors the authoritative decode in ``rmmz_core.js``
(``Tilemap.prototype._addAutotile``, the ``isTileA1`` branch):

* ``local_kind`` spans 0..15 = one A1 autotile per slot.
* **Water autotiles** (kinds 0-3 and every even kind >= 4) compose from
  the full **Floor** source (``FLOOR_AUTOTILE_TABLE``, 48 shapes). The
  engine reads them at ``bx = water_surface_index * 2`` where
  ``water_surface_index = [0, 1, 2, 1][animationFrame % 4]``: each water
  autotile stores **three 96x144 animation frames side by side**. Kinds
  2 and 3 are the exception: the engine reads them at a fixed ``bx = 6``
  without the animation index, so they are **static** (one frame) —
  they are also the two kinds ``Tilemap.isWaterTile`` excludes.
* **Waterfall autotiles** (every odd kind >= 4, per
  ``Tilemap.isWaterfallTile``) compose from the shared
  **Waterfall** source (``WATERFALL_AUTOTILE_TABLE``, 4 shapes). The
  engine reads them at ``bx += 6`` and ``by += animationFrame % 3``:
  each waterfall stores **three 96x48 animation frames stacked
  vertically** (a 96x144 column in total).

The four waterfall shapes differ on their **left/right halves only**
(the two inner quarter columns hold the continuous-water variant, the
two outer columns the exposed-edge variants): waterfalls connect
*horizontally* — the falling water itself is continuous in every
shape. Shape 0 keeps both sides connected, shape 1 exposes the left
edge, shape 2 the right edge and shape 3 is isolated.

Animation timing (``rmmz_core.js``): ``animationFrame =
Math.floor(animationCount / 30)`` — one animation tick lasts 30 game
frames (0.5 s at 60 fps). The water cycle ``[0, 1, 2, 1]`` therefore
maps to Godot frame durations ``(0.5, 1.0, 0.5)`` (2 s cycle, the
duplicated surface index 1 becomes a doubled duration) and the
waterfall cycle ``[0, 1, 2]`` to ``(0.5, 0.5, 0.5)`` (1.5 s cycle).

Tile ID layout: ``TILE_ID_A1 = 2048`` and 48 shape IDs per kind. The
converter stores ``index = (local_kind * 48 + shape) * A1_FRAME_STRIDE
+ frame`` on the TileRef (the frame needs its own atlas tile, so the
plain ``kind * 48 + shape`` encoding cannot distinguish frames); the
engine Tile ID is therefore ``2048 + index // A1_FRAME_STRIDE``.
"""

from collections.abc import Callable, Hashable, Iterator

from PIL import Image

from .composer import QUARTER_SIZE, Quarters
from .shapes import FLOOR_AUTOTILE_TABLE, WATERFALL_AUTOTILE_TABLE
from .unique import unique_tiles

# One water autotile occupies a 96px-wide source slot per animation
# frame; one waterfall occupies a 96x48 slot per frame.
A1_SLOT_WIDTH = 96

# Left edge of a source column / top edge of a source row.
A1_COLUMNS = 8
A1_ROWS = 2

# Number of autotiles in one A1 sheet (local kind 0..15).
A1_AUTOTILE_COUNT = 16

# Canonical outer dimensions of the A1 sheet.
A1_WIDTH = 768
A1_HEIGHT = 576

# RPG Maker reserves exactly 48 Tile IDs per autotile kind. Water
# autotiles use the Floor table (48 shapes); waterfalls use the
# Waterfall table (4 shapes, the remaining shape IDs cycle).
A1_SHAPES_PER_AUTOTILE = 48

# TileRef index encoding: every (kind, shape) composition owns
# A1_FRAME_STRIDE consecutive indexes, one per animation frame
# (static kinds only use the first slot). The RPG Maker Tile ID of a
# tile is ``TILE_ID_A1 + index // A1_FRAME_STRIDE``.
A1_FRAME_STRIDE = 3

# Animation frames per autotile kind: three for every animated water
# and every waterfall, one for the static kinds 2 and 3.
A1_WATER_FRAME_COUNT = 3
A1_WATERFALL_FRAME_COUNT = 3

# Waterfall kinds: every odd kind >= 4 (Tilemap.isWaterfallTile).
A1_WATERFALL_KINDS = frozenset(range(5, 16, 2))

# Static water kinds: the engine reads them without the water-surface
# animation index (and Tilemap.isWaterTile excludes them).
A1_STATIC_KINDS = frozenset((2, 3))

# Animation timing: one engine animation tick lasts 30 game frames
# (Tilemap.update), i.e. 0.5 s at 60 fps. The water surface cycles
# [0, 1, 2, 1] — encoded in Godot as frame durations where the
# repeated frame 1 lasts twice as long — and waterfalls cycle 0, 1, 2.
A1_ANIMATION_TICK = 0.5
A1_WATER_DURATIONS: tuple[float, ...] = (
    A1_ANIMATION_TICK,
    A1_ANIMATION_TICK * 2,
    A1_ANIMATION_TICK,
)
A1_WATERFALL_DURATIONS: tuple[float, ...] = (
    A1_ANIMATION_TICK,
    A1_ANIMATION_TICK,
    A1_ANIMATION_TICK,
)

# Packing of the unfolded A1 tiles inside their atlas region: a 16 tile
# per row grid, so each row is 16 * 48 = 768 px wide (matching the
# width of the other sheets). Animation frames of one composition are
# packed on consecutive slots (Godot's animation frames occupy the
# grid cells right of the base tile) and never straddle two rows.
A1_PACK_COLUMNS = 16
A1_PACK_WIDTH = A1_PACK_COLUMNS * 48


def a1_is_waterfall(
    local_kind: int,
) -> bool:
    """Return whether ``local_kind`` is a waterfall autotile.

    Mirrors ``Tilemap.isWaterfallTile``: only the odd kinds >= 4
    compose from the WATERFALL_AUTOTILE_TABLE; kinds 1 and 3 are waters
    despite being odd.
    """

    if not 0 <= local_kind < A1_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A1_AUTOTILE_COUNT}), got {local_kind}."
        )

    return local_kind in A1_WATERFALL_KINDS


def a1_kind_frames(
    local_kind: int,
) -> int:
    """Return the number of animation frames of one A1 autotile.

    Animated waters (kinds 0, 1 and the even kinds >= 4) and
    waterfalls store three frames; the static waters (kinds 2 and 3)
    store a single frame — the engine reads them without the water
    surface animation index.
    """

    if not 0 <= local_kind < A1_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A1_AUTOTILE_COUNT}), got {local_kind}."
        )

    if local_kind in A1_STATIC_KINDS:
        return 1

    if a1_is_waterfall(local_kind):
        return A1_WATERFALL_FRAME_COUNT

    return A1_WATER_FRAME_COUNT


def a1_animation_durations(
    local_kind: int,
) -> tuple[float, ...] | None:
    """Return the Godot frame durations of one A1 autotile.

    Durations are seconds, matching the engine's animation tick of
    0.5 s (``animationFrame = animationCount / 30``). Waters cycle
    ``[0, 1, 2, 1]``, encoded as ``(0.5, 1.0, 0.5)``; waterfalls cycle
    ``[0, 1, 2]``, encoded as ``(0.5, 0.5, 0.5)``. Static kinds return
    ``None`` — no animation.
    """

    if not 0 <= local_kind < A1_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A1_AUTOTILE_COUNT}), got {local_kind}."
        )

    if local_kind in A1_STATIC_KINDS:
        return None

    if a1_is_waterfall(local_kind):
        return A1_WATERFALL_DURATIONS

    return A1_WATER_DURATIONS


def a1_animation_id(
    local_kind: int,
) -> str:
    """Return the animation family of one A1 autotile.

    ``"water"``, ``"waterfall"`` or ``"static"``. Two compositions may
    only merge during the pixel deduplication when they belong to the
    same family — a water frame and a waterfall frame rendering
    identically would otherwise inherit the wrong animation.
    """

    if not 0 <= local_kind < A1_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A1_AUTOTILE_COUNT}), got {local_kind}."
        )

    if local_kind in A1_STATIC_KINDS:
        return "static"

    if a1_is_waterfall(local_kind):
        return "waterfall"

    return "water"


def a1_kind_region(
    local_kind: int,
) -> tuple[int, int, int, int]:
    """Return ``(source_x, source_y, width, height)`` of one A1 autotile.

    The region covers **every** animation frame of the autotile:
    waters occupy a 288x144 area (three 96x144 frames side by side)
    except the static kinds 2 and 3 (96x144), and waterfalls occupy a
    96x144 column (three 96x48 frames stacked vertically).
    """

    if not 0 <= local_kind < A1_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A1_AUTOTILE_COUNT}), got {local_kind}."
        )

    if local_kind == 0:
        return 0, 0, 3 * A1_SLOT_WIDTH, 144

    if local_kind == 1:
        return 0, 144, 3 * A1_SLOT_WIDTH, 144

    if local_kind == 2:
        return 288, 0, A1_SLOT_WIDTH, 144

    if local_kind == 3:
        return 288, 144, A1_SLOT_WIDTH, 144

    tx = local_kind % 8
    ty = local_kind // 8

    bx = (tx // 4) * 8
    by = ty * 6 + ((tx // 2) % 2) * 3

    if a1_is_waterfall(local_kind):
        # One 96x48 frame per animation tick, stacked vertically.
        return (bx + 6) * 48, by * 48, A1_SLOT_WIDTH, 144

    # Three 96x144 frames side by side (bx, bx+2, bx+4 tile-pairs).
    return bx * 48, by * 48, 3 * A1_SLOT_WIDTH, 144


def a1_source_region(
    local_kind: int,
    frame: int = 0,
) -> tuple[int, int]:
    """Return ``(source_x, source_y)`` of one A1 animation frame.

    ``source_x``/``source_y`` are the pixel top-left of the frame's
    source region in the ``*_A1.png`` (768x576) sheet: a 96x144 region
    for water autotiles (one of the three side-by-side frames) and a
    96x48 region for waterfalls (one of the three stacked frames).

    The mapping is computed from the authoritative ``rmmz_core.js``
    formula (``bx = water_surface_index * 2`` for waters and
    ``bx += 6`` / ``by += animationFrame % 3`` for waterfalls) so it
    stays correct without guessing.
    """

    if not 0 <= local_kind < A1_AUTOTILE_COUNT:
        raise ValueError(
            f"local_kind must be in [0, {A1_AUTOTILE_COUNT}), got {local_kind}."
        )

    frames = a1_kind_frames(local_kind)

    if not 0 <= frame < frames:
        raise ValueError(
            f"frame must be in [0, {frames}) for kind {local_kind}, got {frame}."
        )

    if local_kind == 0:
        return frame * A1_SLOT_WIDTH, 0

    if local_kind == 1:
        return frame * A1_SLOT_WIDTH, 144

    if local_kind == 2:
        return 288, 0

    if local_kind == 3:
        return 288, 144

    tx = local_kind % 8
    ty = local_kind // 8

    bx = (tx // 4) * 8
    by = ty * 6 + ((tx // 2) % 2) * 3

    if a1_is_waterfall(local_kind):
        # bx += 6; by += animationFrame % 3: three 96x48 frames
        # stacked vertically.
        return (bx + 6) * 48, (by + frame) * 48

    # bx += waterSurfaceIndex * 2: three 96x144 frames side by side.
    return (bx + frame * 2) * 48, by * 48


def a1_shape_quarters(
    local_kind: int,
    shape: int,
    frame: int = 0,
) -> Quarters:
    """Return the pieces of one unfolded A1 animation frame.

    Each piece is a ``(qx, qy, dx, dy)`` tuple: ``(qx, qy)`` locates
    the 24px-wide piece in the sheet (absolute pixel coordinates),
    ``(dx, dy)`` places it inside the resulting 48x48 tile.

    ``shape`` runs 0..47 and selects the engine shape table entry —
    ``FLOOR_AUTOTILE_TABLE[shape]`` for water autotiles,
    ``WATERFALL_AUTOTILE_TABLE[shape % 4]`` for waterfalls — matching
    RPG Maker's per-kind Tile ID layout. ``frame`` selects the
    animation frame (one of three, or the single static one).
    """

    source_x, source_y = a1_source_region(local_kind, frame)

    if a1_is_waterfall(local_kind):
        entry = WATERFALL_AUTOTILE_TABLE[shape % len(WATERFALL_AUTOTILE_TABLE)]
    else:
        entry = FLOOR_AUTOTILE_TABLE[shape % len(FLOOR_AUTOTILE_TABLE)]

    pieces: Quarters = tuple(
        (
            source_x + quarter_x * QUARTER_SIZE,
            source_y + quarter_y * QUARTER_SIZE,
            (index % 2) * QUARTER_SIZE,
            (index // 2) * QUARTER_SIZE,
        )
        for index, (quarter_x, quarter_y) in enumerate(entry)
    )

    return pieces


def a1_composition_quarters(
    local_kind: int,
    shape: int,
) -> Quarters:
    """Return the joint pieces of every animation frame of a composition.

    The pieces of all frames are concatenated into one draw-ordered
    tuple whose destinations are shifted by 48px per frame: composing
    it yields the ``48 * frame_count``-wide strip holding the whole
    animation side by side. The pixel deduplication compares these
    strips so two compositions only merge when their **entire frame
    sequence** renders identically — merging a single frame would
    break the animation of the merged kind.
    """

    pieces: list[Quarters] = []

    for frame in range(a1_kind_frames(local_kind)):
        offset = frame * 48

        pieces.append(
            tuple(
                (
                    piece[0],
                    piece[1],
                    piece[2] + offset,
                    piece[3],
                )
                for piece in a1_shape_quarters(local_kind, shape, frame)
            )
        )

    return tuple(piece for frame_pieces in pieces for piece in frame_pieces)


def a1_quarters_from_index(
    index: int,
) -> Quarters:
    """Return the pieces of one unfolded A1 frame from its TileRef index.

    ``index`` encodes ``(local_kind * 48 + shape) * A1_FRAME_STRIDE +
    frame`` (see the module docstring).
    """

    composition, frame = divmod(index, A1_FRAME_STRIDE)

    local_kind, shape = divmod(composition, A1_SHAPES_PER_AUTOTILE)

    return a1_shape_quarters(local_kind, shape, frame)


def a1_unique_compositions() -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for every distinct A1 composition.

    Walks the sheet in engine ID order (kinds 0..15, shapes 0..47),
    yielding the **joint** quarter strips of every (kind, shape)
    composition — all of its animation frames at once. ``index`` is the
    frame-0 TileRef offset
    (``(local_kind * 48 + shape) * A1_FRAME_STRIDE``).

    Waterfall shapes 4..47 cycle the 4-shape Waterfall table: their
    strips repeat shapes 0..3 and are skipped, exactly like the cycled
    shape IDs of the A3/A4 wall table.
    """

    seen: set[Quarters] = set()

    for local_kind in range(A1_AUTOTILE_COUNT):
        for shape in range(A1_SHAPES_PER_AUTOTILE):
            quarters = a1_composition_quarters(local_kind, shape)

            if quarters in seen:
                continue

            seen.add(quarters)

            yield (
                (local_kind * A1_SHAPES_PER_AUTOTILE + shape) * A1_FRAME_STRIDE,
                quarters,
            )


def a1_unique_tiles(
    source: Image.Image,
    *,
    tolerance: int = 0,
    dedup_key: Callable[[int, bytes], Hashable] | None = None,
) -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for each **graphically distinct** tile.

    Walks :func:`a1_unique_compositions` in engine ID order, composes
    every candidate's full animation strip (all frames side by side,
    see :func:`a1_composition_quarters`) and keeps only the first
    occurrence of each distinct pixel content. Two compositions only
    merge when their **whole frame sequence** renders identically —
    and, when a ``dedup_key`` is given, when their keys are equal too.
    The converter passes a key carrying the resolved collision and the
    animation family (see :func:`a1_animation_id`): graphically
    identical tiles with a different passage — or a different animation
    — stay separate.

    With ``tolerance > 0``, two strips are also considered identical
    when they differ by at most ``tolerance`` **pixels** in total
    across all of their frames. The first occurrence is still the tile
    kept. ``tolerance = 0`` (the default) requires byte-exact pixels.

    Yields:
        ``(index, quarters)`` pairs where ``index`` is the frame-0
        TileRef offset of the first occurrence and ``quarters`` the
        joint strip identifying the composition (absolute source
        coordinates, draw order, destinations shifted per frame).
    """

    if tolerance < 0:
        raise ValueError(
            f"tolerance must be >= 0, got {tolerance}."
        )

    return unique_tiles(
        a1_unique_compositions(),
        source,
        tolerance=tolerance,
        dedup_key=dedup_key,
    )


# Number of distinct A1 quarter compositions, one per (kind, shape):
# 48 shapes per water kind (kinds 0-3 and the even kinds >= 4) and 4
# distinct shapes per waterfall (the remaining shape IDs cycle the
# 4-shape Waterfall table): 10 x 48 + 6 x 4 = 504. Each composition
# unfolds into ``a1_kind_frames(kind)`` ready-to-place 48x48 tiles (its
# animation frames), i.e. 8 x 144 + 2 x 48 + 6 x 12 = 1320 tiles for a
# sheet whose every quarter is graphically distinct. Graphically
# identical compositions are merged later by a1_unique_tiles, so the
# packed tile count of a converted sheet is image-dependent and always
# <= 1320.
A1_UNIQUE_COMPOSITION_COUNT = sum(
    1
    for _ in a1_unique_compositions()
)


__all__ = [
    "A1_ANIMATION_TICK",
    "A1_AUTOTILE_COUNT",
    "A1_COLUMNS",
    "A1_FRAME_STRIDE",
    "A1_HEIGHT",
    "A1_PACK_COLUMNS",
    "A1_PACK_WIDTH",
    "A1_ROWS",
    "A1_SHAPES_PER_AUTOTILE",
    "A1_SLOT_WIDTH",
    "A1_UNIQUE_COMPOSITION_COUNT",
    "A1_WATERFALL_DURATIONS",
    "A1_WATERFALL_KINDS",
    "A1_WATER_DURATIONS",
    "A1_WIDTH",
    "a1_animation_durations",
    "a1_animation_id",
    "a1_composition_quarters",
    "a1_is_waterfall",
    "a1_kind_frames",
    "a1_kind_region",
    "a1_quarters_from_index",
    "a1_shape_quarters",
    "a1_source_region",
    "a1_unique_compositions",
    "a1_unique_tiles",
]
