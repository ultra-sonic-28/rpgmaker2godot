"""Graphically-distinct selection shared by the autotile unfolders.

``a3_unique_tiles`` and ``a4_unique_tiles`` walk their sheet's quarter
compositions in engine ID order, compose every candidate into its final
48x48 image and keep only the first occurrence of each distinct pixel
content. The comparison machinery (byte-exact set, optional
pixel-tolerance pre-filter) lives here, parameterised by the candidate
stream, so the A3 and A4 unfolders stay thin wrappers.
"""

from collections.abc import Callable, Hashable, Iterator

from PIL import Image, ImageChops

from .composer import compose_quarters

# One composition: four (qx, qy, dx, dy) 24x24 quarter pieces.
Quarters = tuple[tuple[int, int, int, int], ...]

# Each differing pixel changes a tile's total byte sum by at most
# 4 channels x 255. This bounds the safe pre-filter used by the
# tolerance deduplication.
_MAX_BYTE_DELTA_PER_PIXEL = 4 * 255


def unique_tiles(
    candidates: Iterator[tuple[int, Quarters]],
    source: Image.Image,
    *,
    tolerance: int = 0,
    dedup_key: Callable[[int, bytes], Hashable] | None = None,
) -> Iterator[tuple[int, Quarters]]:
    """Yield ``(index, quarters)`` for each **graphically distinct** tile.

    Walks ``candidates`` in engine ID order, composes every candidate
    into its final 48x48 image and keeps only the first occurrence of
    each distinct pixel content (exact, byte-for-byte comparison of the
    composed RGBA pixels). Two different compositions can still render
    identically when the source quarters they select are visually the
    same — uniform fills are common in stock A3/A4 sheets.

    With ``tolerance > 0``, two tiles are also considered identical
    when they differ by at most ``tolerance`` **pixels** (in any RGBA
    channel). This discards noise inherited from the source sheet,
    where some shape variants differ by one or two stray pixels only.
    The first occurrence is still the tile kept. ``tolerance = 0`` (the
    default) requires byte-exact pixels.

    Args:
        candidates: ``(index, quarters)`` pairs in engine ID order,
            where ``quarters`` is the draw-order tuple of absolute
            source quarter coordinates identifying the composed tile.
        source: The RGBA autotile source sheet image.
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
        ``(index, quarters)`` pairs where ``index`` is the engine ID of
        the first occurrence and ``quarters`` the identifying
        composition (absolute source coordinates, draw order).
    """

    if tolerance < 0:
        raise ValueError(
            f"tolerance must be >= 0, got {tolerance}."
        )

    # Exact matches resolve through a set: O(1) per candidate. In
    # tolerance mode a dropped candidate is recorded too, so a later
    # candidate with the very same pixels short-circuits.
    seen_exact: set[tuple[bytes, Hashable]] = set()

    # Tolerance matches need the kept tiles' pixels: they live until
    # the generator is exhausted, then get closed. Kept tiles are
    # indexed by byte-sum bucket (see _find_tolerance_duplicate).
    kept: list[tuple[Hashable, int]] = []
    kept_images: list[Image.Image] = []
    buckets: dict[int, list[int]] = {}
    bucket_width = tolerance * _MAX_BYTE_DELTA_PER_PIXEL + 1

    try:
        for index, quarters in candidates:
            tile = compose_quarters(source, quarters)

            signature = tile.tobytes()

            key = (
                dedup_key(index, signature)
                if dedup_key is not None
                else None
            )

            if (signature, key) in seen_exact:
                tile.close()
                continue

            duplicate = False

            if tolerance > 0:
                duplicate = _find_tolerance_duplicate(
                    tile,
                    signature,
                    key,
                    tolerance=tolerance,
                    bucket_width=bucket_width,
                    kept=kept,
                    kept_images=kept_images,
                    buckets=buckets,
                )

            seen_exact.add((signature, key))

            if duplicate:
                tile.close()
                continue

            if tolerance > 0:
                tile_sum = sum(signature)
                kept.append((key, tile_sum))
                kept_images.append(tile)
                buckets.setdefault(
                    tile_sum // bucket_width,
                    [],
                ).append(len(kept) - 1)
            else:
                tile.close()

            yield index, quarters
    finally:
        for image in kept_images:
            image.close()


def _pixel_difference_count(
    first: Image.Image,
    second: Image.Image,
) -> int:
    """Count the pixels differing in any RGBA channel between two tiles."""

    difference = ImageChops.difference(first, second)

    red, green, blue, alpha = difference.split()

    any_channel = ImageChops.lighter(
        ImageChops.lighter(red, green),
        ImageChops.lighter(blue, alpha),
    )

    return sum(any_channel.histogram()[1:])


def _find_tolerance_duplicate(
    tile: Image.Image,
    signature: bytes,
    key: Hashable,
    *,
    tolerance: int,
    bucket_width: int,
    kept: list[tuple[Hashable, int]],
    kept_images: list[Image.Image],
    buckets: dict[int, list[int]],
) -> bool:
    """Return whether ``tile`` matches a kept tile within tolerance.

    Only kept tiles whose byte sum is close enough to ``tile``'s are
    compared pixel by pixel: two tiles differing by at most
    ``tolerance`` pixels cannot differ by more than
    ``tolerance * _MAX_BYTE_DELTA_PER_PIXEL`` in total byte sum, so the
    pre-filter never hides a match. The ``key`` must also be equal.
    """

    tile_sum = sum(signature)

    bucket = tile_sum // bucket_width

    candidates = (
        buckets.get(bucket - 1, [])
        + buckets.get(bucket, [])
        + buckets.get(bucket + 1, [])
    )

    max_sum_delta = tolerance * _MAX_BYTE_DELTA_PER_PIXEL

    for kept_index in candidates:
        kept_key, kept_sum = kept[kept_index]

        if kept_key != key:
            continue

        if abs(kept_sum - tile_sum) > max_sum_delta:
            continue

        if (
            _pixel_difference_count(kept_images[kept_index], tile)
            <= tolerance
        ):
            return True

    return False


__all__ = [
    "Quarters",
    "unique_tiles",
]