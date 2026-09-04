"""Compose RPG Maker autotiles from their 24x24 source quarters.

RPG Maker does not store the 16 (or 48) connection variants of an
autotile as ready-made images. Instead it stores one autotile **source**
(a multi-quarter region) plus a shape table that selects which four
24x24 quarters form each 48x48 finished tile.

This module materialises the finished tiles from a source region, which
is exactly what the converter needs for the "unfolded autotile"
pipeline: each generated tile is a real, ready-to-paste 48x48 image.
"""

from PIL import Image

from .shapes import (
    FLOOR_AUTOTILE_TABLE,
    WALL_AUTOTILE_TABLE,
    AutotileShape,
)

QUARTER_SIZE = 24
TILE_SIZE = 48

# One quarter piece: ``(qx, qy, dx, dy)`` selects a full 24x24 quarter;
# the optional fifth element narrows the piece to the top ``height``
# pixels of that quarter (12px halves, used by the A2 table rendering).
QuarterPiece = tuple[int, int, int, int] | tuple[int, int, int, int, int]

# One composition: a draw-ordered tuple of quarter pieces.
Quarters = tuple[QuarterPiece, ...]


def compose_autotile(
    source: Image.Image,
    *,
    source_x: int,
    source_y: int,
    shape: AutotileShape,
) -> Image.Image:
    """Build one 48x48 tile by pasting four source quarters.

    Args:
        source: The RGBA autotile source image.
        source_x: Pixel x of the autotile source region's top-left in
            ``source``.
        source_y: Pixel y of the autotile source region's top-left in
            ``source``.
        shape: Four ``(quarter_x, quarter_y)`` coordinates in
            (top-left, top-right, bottom-left, bottom-right) order.

    Returns:
        A new 48x48 RGBA image assembled from the four quarters.
    """

    if len(shape) != 4:
        raise ValueError(
            f"An autotile shape must pick exactly 4 quarters, got {len(shape)}."
        )

    tile = Image.new(
        "RGBA",
        (TILE_SIZE, TILE_SIZE),
        (0, 0, 0, 0),
    )

    for index, (quarter_x, quarter_y) in enumerate(shape):
        left = source_x + quarter_x * QUARTER_SIZE
        top = source_y + quarter_y * QUARTER_SIZE

        quarter = source.crop(
            (
                left,
                top,
                left + QUARTER_SIZE,
                top + QUARTER_SIZE,
            )
        )

        dest_x = (index % 2) * QUARTER_SIZE
        dest_y = (index // 2) * QUARTER_SIZE

        tile.alpha_composite(
            quarter,
            (dest_x, dest_y),
        )

        quarter.close()

    return tile


def compose_quarters(
    source: Image.Image,
    quarters: Quarters,
) -> Image.Image:
    """Build one 48x48 tile from absolute quarter coordinates.

    ``quarters`` is a draw-ordered tuple of ``(qx, qy, dx, dy)`` (or
    ``(qx, qy, dx, dy, height)``) pieces, as produced by
    ``a2_shape_quarters`` / ``a3_shape_quarters`` / ``a4_shape_quarters``:
    ``(qx, qy)`` locates the piece in ``source`` (absolute pixel
    coordinates) and ``(dx, dy)`` places it inside the resulting tile.
    A piece is 24px wide; its height is 24px (a full quarter) or, when
    the fifth element is given, exactly that many pixels cropped from
    the top of the quarter (12px halves, used by the A2 table
    rendering).

    Returns:
        A new 48x48 RGBA image assembled from the quarter pieces.
    """

    if not quarters:
        raise ValueError(
            "An autotile tile must pick at least one quarter piece."
        )

    tile = Image.new(
        "RGBA",
        (TILE_SIZE, TILE_SIZE),
        (0, 0, 0, 0),
    )

    for piece in quarters:
        if len(piece) == 5:
            quarter_x, quarter_y, dest_x, dest_y, piece_height = piece
        else:
            quarter_x, quarter_y, dest_x, dest_y = piece
            piece_height = QUARTER_SIZE

        piece_image = source.crop(
            (
                quarter_x,
                quarter_y,
                quarter_x + QUARTER_SIZE,
                quarter_y + piece_height,
            )
        )

        tile.alpha_composite(
            piece_image,
            (dest_x, dest_y),
        )

        piece_image.close()

    return tile


def unfold_autotile(
    source: Image.Image,
    *,
    source_x: int,
    source_y: int,
    table: tuple[AutotileShape, ...] = WALL_AUTOTILE_TABLE,
) -> tuple[Image.Image, ...]:
    """Unfold one autotile source into its ready-to-paste variants.

    Every entry of ``table`` is composed into a 48x48 tile. ``table``
    defaults to :data:`WALL_AUTOTILE_TABLE` (16 shapes, the A4 "Wall
    Side"); pass :data:`FLOOR_AUTOTILE_TABLE` (48 shapes, the A4 "Wall
    Top") to unfold a full autotile.
    """

    return tuple(
        compose_autotile(
            source,
            source_x=source_x,
            source_y=source_y,
            shape=shape,
        )
        for shape in table
    )


def unfold_wall_autotile(
    source: Image.Image,
    *,
    source_x: int,
    source_y: int,
) -> tuple[Image.Image, ...]:
    """Return the 16 wall-autotile variants of one A4 "Wall Side"."""

    return unfold_autotile(
        source,
        source_x=source_x,
        source_y=source_y,
        table=WALL_AUTOTILE_TABLE,
    )


def unfold_floor_autotile(
    source: Image.Image,
    *,
    source_x: int,
    source_y: int,
) -> tuple[Image.Image, ...]:
    """Return the 48 full-autotile variants of one A4 "Wall Top"."""

    return unfold_autotile(
        source,
        source_x=source_x,
        source_y=source_y,
        table=FLOOR_AUTOTILE_TABLE,
    )