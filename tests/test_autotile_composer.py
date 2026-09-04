import pytest
from PIL import Image

from rpgmaker2godot.tileset.autotile import (
    FLOOR_AUTOTILE_TABLE,
    QUARTER_SIZE,
    TILE_SIZE,
    WALL_AUTOTILE_TABLE,
    compose_autotile,
    compose_quarters,
    unfold_floor_autotile,
    unfold_wall_autotile,
)
from rpgmaker2godot.tileset.autotile.a2 import (
    A2_HEIGHT,
    A2_WIDTH,
    a2_shape_quarters,
    a2_source_region,
    a2_unique_tiles,
)
from rpgmaker2godot.tileset.autotile.a3 import a3_source_region, a3_unique_tiles
from rpgmaker2godot.tileset.autotile.a4 import a4_source_region, a4_unique_tiles


def _quarter_colour(quarter_x: int, quarter_y: int) -> tuple[int, int, int, int]:
    """A uniform colour uniquely identifying one 24x24 quarter."""
    return (quarter_x * 50, quarter_y * 50, 0, 255)


def _make_source() -> Image.Image:
    """Synthetic 96x96 source: each 24x24 quarter gets a unique colour."""
    return _make_source_96(4, 4)


def _make_source_96(quarter_cols: int, quarter_rows: int) -> Image.Image:
    """Synthetic 96x(quarter_rows*24) source with unique quarter colours."""
    source = Image.new(
        "RGBA",
        (quarter_cols * QUARTER_SIZE, quarter_rows * QUARTER_SIZE),
    )
    for qy in range(quarter_rows):
        for qx in range(quarter_cols):
            colour = _quarter_colour(qx, qy)
            for dy in range(QUARTER_SIZE):
                for dx in range(QUARTER_SIZE):
                    source.putpixel(
                        (qx * QUARTER_SIZE + dx, qy * QUARTER_SIZE + dy),
                        colour,
                    )
    return source


def _assert_quarter_colour(
    tile: Image.Image,
    shape: object,
    index: int,
) -> None:
    shape = tuple(shape)
    quarter_x, quarter_y = shape[index]
    ox = (index % 2) * QUARTER_SIZE
    oy = (index // 2) * QUARTER_SIZE
    expected = _quarter_colour(quarter_x, quarter_y)
    for y in range(oy, oy + QUARTER_SIZE):
        for x in range(ox, ox + QUARTER_SIZE):
            assert tile.getpixel((x, y)) == expected


def test_shape_0_selects_central_quarters() -> None:
    source = _make_source()
    tile = compose_autotile(
        source,
        source_x=0,
        source_y=0,
        shape=WALL_AUTOTILE_TABLE[0],
    )

    # shape 0 = [[2,2],[1,2],[2,1],[1,1]]
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[0], 0)
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[0], 1)
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[0], 2)
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[0], 3)

    source.close()
    tile.close()


def test_unfold_wall_autotile_yields_16_distinct_tiles() -> None:
    source = _make_source()
    tiles = unfold_wall_autotile(source, source_x=0, source_y=0)

    assert len(tiles) == 16

    # Each variant is 48x48.
    assert all(t.size == (TILE_SIZE, TILE_SIZE) for t in tiles)

    # All 16 shapes must produce visually different tiles.
    rendered = [t.tobytes() for t in tiles]
    assert len(set(rendered)) == 16

    for t in tiles:
        t.close()

    source.close()


def test_unfold_respects_source_offset() -> None:
    """Providing a non-zero source origin shifts the quarters."""
    source = _make_source()
    # Place the classic 'shape 3' (the four inner corners TL/TL...) far.
    # Use a source region origin of (0, 0) and a shape that references
    # (3,3): verify the returned tile equals the expected quarter.
    tile = compose_autotile(
        source,
        source_x=0,
        source_y=0,
        shape=WALL_AUTOTILE_TABLE[15],  # [[0,0],[3,0],[0,3],[3,3]]
    )

    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[15], 0)
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[15], 1)
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[15], 2)
    _assert_quarter_colour(tile, WALL_AUTOTILE_TABLE[15], 3)

    source.close()
    tile.close()


def test_short_shape_is_rejected() -> None:
    source = _make_source()

    with pytest.raises(ValueError):
        compose_autotile(
            source,
            source_x=0,
            source_y=0,
            shape=((0, 0), (1, 0), (0, 1)),
        )

    source.close()


def test_floor_table_has_48_shapes() -> None:
    assert len(FLOOR_AUTOTILE_TABLE) == 48
    assert len(WALL_AUTOTILE_TABLE) == 16


def test_unfold_floor_autotile_yields_48_tiles() -> None:
    # The floor (Wall Top) autotile uses quarter rows up to y=5 -> 144px.
    source = _make_source_96(4, 6)

    tiles = unfold_floor_autotile(source, source_x=0, source_y=0)

    assert len(tiles) == 48
    assert all(t.size == (TILE_SIZE, TILE_SIZE) for t in tiles)

    # The 48 shapes should span a wide visual variety.
    rendered = [t.tobytes() for t in tiles]
    assert len(set(rendered)) > 1

    for t in tiles:
        t.close()

    source.close()


def test_a4_source_region_maps_slots() -> None:
    # Column 0, topmost row (Wall Top).
    assert a4_source_region(0) == (0, 0, False)

    # Column 7 (last), same top row: Wall Top at (7*96, 0).
    assert a4_source_region(7) == (672, 0, False)

    # Column 0, second row (Wall Side) at (0, 3*48=144).
    assert a4_source_region(8) == (0, 144, True)

    # Column 3 (tx=3), row 3 (ty=13 -> by=8): Wall Side at (288, 384).
    assert a4_source_region(3 * 8 + 3) == (288, 384, True)

    # Last autotile (slot 47): tx=7, row5 -> Wall Side at (7*96, 13*48).
    assert a4_source_region(47) == (672, 624, True)


def test_a4_unique_compositions_deduplicates_wall_sides() -> None:
    """The 2304 raw A4 shape IDs reduce to 1536 distinct compositions."""

    from collections import Counter

    from rpgmaker2godot.tileset.autotile.a4 import (
        A4_SHAPES_PER_AUTOTILE,
        A4_UNIQUE_COMPOSITION_COUNT,
        a4_shape_quarters,
        a4_unique_compositions,
    )

    unique = list(a4_unique_compositions())

    assert A4_UNIQUE_COMPOSITION_COUNT == 1536
    assert len(unique) == 1536

    # First occurrences, emitted in ascending engine ID order.
    indexes = [index for index, _quarters in unique]
    assert indexes == sorted(indexes)

    # Each entry matches its (kind, shape) decoding.
    for index, quarters in unique:
        kind, shape = divmod(index, A4_SHAPES_PER_AUTOTILE)
        assert quarters == a4_shape_quarters(kind, shape)

    # No composition is emitted twice.
    compositions = {quarters for _index, quarters in unique}
    assert len(compositions) == len(unique)

    # Every kind contributes either its 48 Wall Top shapes or its 16
    # Wall Side shapes.
    per_kind = Counter(
        index // A4_SHAPES_PER_AUTOTILE for index, _quarters in unique
    )
    assert sorted(set(per_kind.values())) == [16, 48]
    wall_top_kinds = sum(1 for count in per_kind.values() if count == 48)
    wall_side_kinds = sum(1 for count in per_kind.values() if count == 16)
    assert (wall_top_kinds, wall_side_kinds) == (24, 24)


def test_a4_unique_tiles_merges_graphically_identical_tiles() -> None:
    """Compositions that render identically collapse to one tile.

    A fully uniform A4 sheet makes every 24x24 quarter identical: all
    2304 raw variants compose the exact same 48x48 tile, so a single
    entry survives — the first engine ID (kind 0, shape 0).
    """

    from rpgmaker2godot.tileset.autotile.a4 import a4_shape_quarters

    source = Image.new("RGBA", (768, 720), (90, 90, 90, 255))

    unique = list(a4_unique_tiles(source))

    assert len(unique) == 1

    index, quarters = unique[0]

    assert index == 0
    assert quarters == a4_shape_quarters(0, 0)

    source.close()


def test_a4_unique_tiles_keeps_all_distinct_compositions() -> None:
    """Injective quarters: pixel dedup behaves like composition dedup.

    When every 24x24 quarter of the sheet is visually unique, two
    compositions can only render identically if they select the same
    quarters — already removed by a4_unique_compositions. The pixel
    pass must therefore keep exactly the same 1536 entries.
    """

    from rpgmaker2godot.tileset.autotile.a4 import a4_unique_compositions

    source = Image.new("RGBA", (768, 720))

    for y in range(0, 720, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            source.paste(
                (
                    (qx * 37) % 256,
                    (qy * 61) % 256,
                    (qx + qy * 3) % 256,
                    255,
                ),
                (x, y, x + 24, y + 24),
            )

    unique = list(a4_unique_tiles(source))

    assert len(unique) == 1536
    assert [index for index, _ in unique] == [
        index for index, _ in a4_unique_compositions()
    ]

    source.close()


def test_a4_unique_tiles_accepts_custom_dedup_key() -> None:
    """A custom key replaces the pixel signature as the identity."""

    from rpgmaker2godot.tileset.autotile.a4 import (
        A4_UNIQUE_COMPOSITION_COUNT,
    )

    source = Image.new("RGBA", (768, 720), (90, 90, 90, 255))

    unique = list(
        a4_unique_tiles(
            source,
            dedup_key=lambda index, signature: index,
        )
    )

    # Keying by engine index keeps every composition alive.
    assert len(unique) == A4_UNIQUE_COMPOSITION_COUNT

    source.close()


def test_a4_unique_tiles_rejects_negative_tolerance() -> None:
    """A negative tolerance is rejected before any composition runs."""

    source = Image.new("RGBA", (96, 96), (90, 90, 90, 255))

    with pytest.raises(ValueError):
        list(a4_unique_tiles(source, tolerance=-1))

    source.close()


def test_a4_unique_tiles_tolerance_merges_noisy_variants() -> None:
    """Variants differing by a few stray pixels merge within tolerance.

    A uniform sheet plus one changed pixel makes exactly one shape
    (kind 0, shape 47 — the only one selecting the quarter containing
    that pixel) differ from all the others by a single pixel: exact
    dedup keeps both tiles, tolerance 1 keeps only the first.
    """

    from rpgmaker2godot.tileset.autotile.a4 import a4_shape_quarters

    source = Image.new("RGBA", (768, 720), (90, 90, 90, 255))
    source.putpixel((5, 5), (255, 0, 0, 255))

    exact = list(a4_unique_tiles(source))

    assert [index for index, _ in exact] == [0, 47]
    assert exact[1][1] == a4_shape_quarters(0, 47)

    tolerant = list(a4_unique_tiles(source, tolerance=1))

    assert len(tolerant) == 1
    assert tolerant[0][0] == 0
    assert tolerant[0][1] == a4_shape_quarters(0, 0)

    source.close()


def test_a3_source_region_maps_slots() -> None:
    # Column 0, topmost row (Roof, band 1).
    assert a3_source_region(0) == (0, 0)

    # Column 7 (last), same top row: Roof at (7*96, 0).
    assert a3_source_region(7) == (672, 0)

    # Column 0, second row (Wall) at (0, 96).
    assert a3_source_region(8) == (0, 96)

    # Column 3, row 3 (Wall, band 2): (3*96, 3*96).
    assert a3_source_region(3 * 8 + 3) == (288, 288)

    # Last autotile (slot 31): tx=7, Wall of band 2 at (7*96, 3*96).
    assert a3_source_region(31) == (672, 288)


def test_a3_source_region_rejects_out_of_range_kinds() -> None:
    from rpgmaker2godot.tileset.autotile.a3 import A3_AUTOTILE_COUNT

    with pytest.raises(ValueError):
        a3_source_region(A3_AUTOTILE_COUNT)

    with pytest.raises(ValueError):
        a3_source_region(-1)


def test_a3_shape_quarters_use_the_wall_table() -> None:
    """Every A3 autotile — Roof or Wall — cycles WALL_AUTOTILE_TABLE."""

    from rpgmaker2godot.tileset.autotile.a3 import a3_shape_quarters

    # Shape 0 = ((2, 2), (1, 2), (2, 1), (1, 1)), offset by the source
    # region of kind 5: (5*96, 0) = (480, 0).
    quarters = a3_shape_quarters(5, 0)

    assert quarters[0] == (480 + 2 * QUARTER_SIZE, 0 + 2 * QUARTER_SIZE, 0, 0)
    assert quarters[3] == (
        480 + 1 * QUARTER_SIZE,
        0 + 1 * QUARTER_SIZE,
        QUARTER_SIZE,
        QUARTER_SIZE,
    )

    # Shape 47 cycles back to the wall table's shape 15.
    assert a3_shape_quarters(0, 47) == a3_shape_quarters(0, 15)

    # Shapes 16..47 duplicate shapes 0..15.
    for shape in range(16, 48):
        assert a3_shape_quarters(2, shape) == a3_shape_quarters(
            2,
            shape - 16,
        )


def test_a3_unique_compositions_yield_512_tiles() -> None:
    """The 1536 raw A3 shape IDs reduce to 512 distinct compositions."""

    from collections import Counter

    from rpgmaker2godot.tileset.autotile.a3 import (
        A3_SHAPES_PER_AUTOTILE,
        A3_UNIQUE_COMPOSITION_COUNT,
        a3_shape_quarters,
        a3_unique_compositions,
    )

    unique = list(a3_unique_compositions())

    assert A3_UNIQUE_COMPOSITION_COUNT == 512
    assert len(unique) == 512

    # First occurrences, emitted in ascending engine ID order.
    indexes = [index for index, _quarters in unique]
    assert indexes == sorted(indexes)

    # Each entry matches its (kind, shape) decoding.
    for index, quarters in unique:
        kind, shape = divmod(index, A3_SHAPES_PER_AUTOTILE)
        assert quarters == a3_shape_quarters(kind, shape)

    # No composition is emitted twice.
    compositions = {quarters for _index, quarters in unique}
    assert len(compositions) == len(unique)

    # Every kind contributes exactly its 16 distinct wall shapes.
    per_kind = Counter(
        index // A3_SHAPES_PER_AUTOTILE for index, _quarters in unique
    )
    assert sorted(set(per_kind.values())) == [16]
    assert len(per_kind) == 32


def test_a3_unique_tiles_merges_graphically_identical_tiles() -> None:
    """Compositions that render identically collapse to one tile.

    A fully uniform A3 sheet makes every 24x24 quarter identical: all
    1536 raw variants compose the exact same 48x48 tile, so a single
    entry survives — the first engine ID (kind 0, shape 0).
    """

    from rpgmaker2godot.tileset.autotile.a3 import a3_shape_quarters

    source = Image.new("RGBA", (768, 384), (90, 90, 90, 255))

    unique = list(a3_unique_tiles(source))

    assert len(unique) == 1

    index, quarters = unique[0]

    assert index == 0
    assert quarters == a3_shape_quarters(0, 0)

    source.close()


def test_a3_unique_tiles_keeps_all_distinct_compositions() -> None:
    """Injective quarters: pixel dedup behaves like composition dedup.

    When every 24x24 quarter of the sheet is visually unique, two
    compositions can only render identically if they select the same
    quarters — already removed by a3_unique_compositions. The pixel
    pass must therefore keep exactly the same 512 entries.
    """

    from rpgmaker2godot.tileset.autotile.a3 import a3_unique_compositions

    source = Image.new("RGBA", (768, 384))

    for y in range(0, 384, 24):
        for x in range(0, 768, 24):
            qx, qy = x // 24, y // 24

            source.paste(
                (
                    (qx * 37) % 256,
                    (qy * 61) % 256,
                    (qx + qy * 3) % 256,
                    255,
                ),
                (x, y, x + 24, y + 24),
            )

    unique = list(a3_unique_tiles(source))

    assert len(unique) == 512
    assert [index for index, _ in unique] == [
        index for index, _ in a3_unique_compositions()
    ]

    source.close()


def test_a3_unique_tiles_accepts_custom_dedup_key() -> None:
    """A custom key replaces the pixel signature as the identity."""

    from rpgmaker2godot.tileset.autotile.a3 import (
        A3_UNIQUE_COMPOSITION_COUNT,
    )

    source = Image.new("RGBA", (768, 384), (90, 90, 90, 255))

    unique = list(
        a3_unique_tiles(
            source,
            dedup_key=lambda index, signature: index,
        )
    )

    # Keying by engine index keeps every composition alive.
    assert len(unique) == A3_UNIQUE_COMPOSITION_COUNT

    source.close()


def test_a3_unique_tiles_rejects_negative_tolerance() -> None:
    """A negative tolerance is rejected before any composition runs."""

    source = Image.new("RGBA", (96, 96), (90, 90, 90, 255))

    with pytest.raises(ValueError):
        list(a3_unique_tiles(source, tolerance=-1))

    source.close()


def test_a3_unique_tiles_tolerance_merges_noisy_variants() -> None:
    """Variants differing by a few stray pixels merge within tolerance.

    A uniform sheet plus one changed pixel at (5, 5) — inside the
    quarter (0, 0) — makes the wall shapes selecting that quarter
    (kind 0, shapes 3, 7, 11 and 15) differ from the uniform ones.
    Their three remaining quarters are uniform either way, so those
    four variants render identically: exact dedup keeps two tiles (the
    uniform one and the first noisy one), tolerance 1 keeps only the
    first.
    """

    from rpgmaker2godot.tileset.autotile.a3 import a3_shape_quarters

    source = Image.new("RGBA", (768, 384), (90, 90, 90, 255))
    source.putpixel((5, 5), (255, 0, 0, 255))

    exact = list(a3_unique_tiles(source))

    assert [index for index, _ in exact] == [0, 3]
    assert exact[1][1] == a3_shape_quarters(0, 3)

    tolerant = list(a3_unique_tiles(source, tolerance=1))

    assert len(tolerant) == 1
    assert tolerant[0][0] == 0
    assert tolerant[0][1] == a3_shape_quarters(0, 0)

    source.close()


def test_a2_source_region_maps_slots() -> None:
    # Column 0, topmost row.
    assert a2_source_region(0) == (0, 0)

    # Column 1 (tx=1), same row: (1*96, 0).
    assert a2_source_region(1) == (96, 0)

    # Column 0, second row: (0, 1*144).
    assert a2_source_region(8) == (0, 144)

    # Column 4, row 3: (4*96, 3*144).
    assert a2_source_region(3 * 8 + 4) == (384, 432)

    # Last autotile (slot 31): tx=7, ty=3: (7*96, 3*144).
    assert a2_source_region(31) == (672, 432)


def test_a2_source_region_rejects_out_of_range_kinds() -> None:
    from rpgmaker2godot.tileset.autotile.a2 import A2_AUTOTILE_COUNT

    with pytest.raises(ValueError):
        a2_source_region(A2_AUTOTILE_COUNT)

    with pytest.raises(ValueError):
        a2_source_region(-1)


def test_a2_shape_quarters_use_the_floor_table() -> None:
    """A2 sources span 6 quarter rows and compose FLOOR_AUTOTILE_TABLE."""

    # Shape 0 = ((2, 4), (1, 4), (2, 3), (1, 3)), offset by the source
    # region of kind 1: (96, 0).
    quarters = a2_shape_quarters(1, 0)

    assert quarters[0] == (
        96 + 2 * QUARTER_SIZE,
        0 + 4 * QUARTER_SIZE,
        0,
        0,
        QUARTER_SIZE,
    )
    assert quarters[3] == (
        96 + 1 * QUARTER_SIZE,
        0 + 3 * QUARTER_SIZE,
        QUARTER_SIZE,
        QUARTER_SIZE,
        QUARTER_SIZE,
    )

    # Shape 47 selects the top-left corner quarters of the source.
    quarters_47 = a2_shape_quarters(2, 47)

    assert quarters_47[0] == (192, 0, 0, 0, QUARTER_SIZE)


def test_a2_table_shape_replaces_outer_quarter_rows() -> None:
    """Table kinds render rows 1/5 quarters through the row-3 surface.

    Shape 8 = ((2, 4), (1, 4), (2, 1), (1, 3)). Its third quarter —
    (2, 1), in quarter row 1 — is replaced by the full mirrored row-3
    quarter (qsx2 = (4 - 2) % 4 = 2) with the top half of the original
    quarter redrawn over its bottom half. The other quarters are
    untouched.
    """

    plain = a2_shape_quarters(0, 8)
    table = a2_shape_quarters(0, 8, is_table=True)

    # The two quarters outside rows 1/5 are unchanged.
    assert table[0] == plain[0]
    assert table[1] == plain[1]
    assert table[4] == plain[3]

    # Row-1 quarter: full mirrored surface quarter...
    assert table[2] == (
        2 * QUARTER_SIZE,
        3 * QUARTER_SIZE,
        0,
        24,
        QUARTER_SIZE,
    )

    # ...then the top half of the original quarter at dest y + 12.
    assert table[3] == (2 * QUARTER_SIZE, 1 * QUARTER_SIZE, 0, 36, 12)


def test_a2_table_shape_keeps_row_5_quarters_unmirrored() -> None:
    """Row 1 quarters are mirrored; row 5 quarters keep their column.

    Shape 33 = ((2, 2), (1, 2), (2, 5), (1, 5)): its two bottom
    quarters sit in quarter row 5, whose surface replacements reuse
    their own column (qsx2 = qsx).
    """

    table = a2_shape_quarters(0, 33, is_table=True)

    assert table[2] == (2 * QUARTER_SIZE, 3 * QUARTER_SIZE, 0, 24, QUARTER_SIZE)
    assert table[3] == (2 * QUARTER_SIZE, 5 * QUARTER_SIZE, 0, 36, 12)

    assert table[4] == (1 * QUARTER_SIZE, 3 * QUARTER_SIZE, 24, 24, QUARTER_SIZE)
    assert table[5] == (1 * QUARTER_SIZE, 5 * QUARTER_SIZE, 24, 36, 12)


def test_a2_composes_table_tile_like_the_engine() -> None:
    """The table composition redraws the affected quarter cell halves."""

    source = _make_source_96(4, 6)

    tile = compose_quarters(source, a2_shape_quarters(0, 8, is_table=True))

    # Bottom-left quarter cell (dest 0, 24): its top half shows the
    # row-3 quarter of column 2, its bottom half the top half of the
    # original (2, 1) quarter.
    assert tile.getpixel((12, 30)) == _quarter_colour(2, 3)
    assert tile.getpixel((12, 40)) == _quarter_colour(2, 1)

    # Unaffected quarter cells keep the plain composition.
    assert tile.getpixel((12, 12)) == _quarter_colour(2, 4)
    assert tile.getpixel((36, 12)) == _quarter_colour(1, 4)
    assert tile.getpixel((36, 36)) == _quarter_colour(1, 3)

    tile.close()
    source.close()


def test_a2_composes_plain_tile_when_not_a_table() -> None:
    """Without the counter flag every quarter is pasted whole."""

    source = _make_source_96(4, 6)

    tile = compose_quarters(source, a2_shape_quarters(0, 8))

    # The bottom-left quarter cell shows the whole (2, 1) quarter.
    assert tile.getpixel((12, 30)) == _quarter_colour(2, 1)
    assert tile.getpixel((12, 40)) == _quarter_colour(2, 1)

    tile.close()
    source.close()


def test_a2_unique_compositions_yield_1536_tiles() -> None:
    """The 1536 raw A2 shape IDs are all distinct compositions."""

    from collections import Counter

    from rpgmaker2godot.tileset.autotile.a2 import (
        A2_SHAPES_PER_AUTOTILE,
        A2_UNIQUE_COMPOSITION_COUNT,
        a2_unique_compositions,
    )

    unique = list(a2_unique_compositions())

    assert A2_UNIQUE_COMPOSITION_COUNT == 1536
    assert len(unique) == 1536

    # First occurrences, emitted in ascending engine ID order.
    indexes = [index for index, _quarters in unique]
    assert indexes == sorted(indexes)

    # Every kind contributes its 48 shapes (no wall-table cycling).
    per_kind = Counter(
        index // A2_SHAPES_PER_AUTOTILE for index, _quarters in unique
    )
    assert sorted(set(per_kind.values())) == [48]
    assert len(per_kind) == 32

    # No composition is emitted twice.
    compositions = {quarters for _index, quarters in unique}
    assert len(compositions) == len(unique)


def test_a2_unique_compositions_with_table_kinds() -> None:
    """Table kinds compose the table variant of their quarter sets."""

    from rpgmaker2godot.tileset.autotile.a2 import a2_unique_compositions

    unique = dict(a2_unique_compositions(table_kinds=(5,)))

    # Kind 5's compositions equal the table variant, kind 0's the
    # plain one.
    assert unique[5 * 48 + 8] == a2_shape_quarters(5, 8, is_table=True)
    assert unique[0 * 48 + 8] == a2_shape_quarters(0, 8, is_table=False)


def test_a2_unique_tiles_merges_graphically_identical_tiles() -> None:
    """Compositions that render identically collapse to one tile.

    A fully uniform A2 sheet makes every 24x24 quarter identical: all
    1536 raw variants compose the exact same 48x48 tile, so a single
    entry survives — the first engine ID (kind 0, shape 0).
    """

    source = Image.new("RGBA", (A2_WIDTH, A2_HEIGHT), (90, 90, 90, 255))

    unique = list(a2_unique_tiles(source))

    assert len(unique) == 1

    index, quarters = unique[0]

    assert index == 0
    assert quarters == a2_shape_quarters(0, 0)

    source.close()


def _make_a2_sheet() -> Image.Image:
    """Synthetic 768x576 A2 sheet with injective quarter colours.

    Every 24x24 quarter of the whole sheet receives a colour derived
    from its (qx, qy) position; the mapping is injective, so two
    compositions render identically only when they select the exact
    same quarters.
    """

    sheet = Image.new("RGBA", (A2_WIDTH, A2_HEIGHT))

    for qy in range(A2_HEIGHT // QUARTER_SIZE):
        for qx in range(A2_WIDTH // QUARTER_SIZE):
            colour = (
                (qx * 7) % 256,
                (qy * 10) % 256,
                (qx + qy) % 256,
                255,
            )

            sheet.paste(
                colour,
                (
                    qx * QUARTER_SIZE,
                    qy * QUARTER_SIZE,
                    (qx + 1) * QUARTER_SIZE,
                    (qy + 1) * QUARTER_SIZE,
                ),
            )

    return sheet


def test_a2_unique_tiles_keeps_table_variants_distinct() -> None:
    """A table kind composes the table variant of every shape.

    On a sheet whose every quarter is drawn (injective quarter
    colours), all 1536 compositions stay alive either way, but kind 0
    marked as a table composes the table variant of its shapes.
    """

    source = _make_a2_sheet()

    plain = list(a2_unique_tiles(source))
    table = list(a2_unique_tiles(source, table_kinds=(0,)))

    # Every shape survives either way (injective quarter colours).
    assert len(plain) == 1536
    assert len(table) == 1536

    # But kind 0's shape-8 composition is the table variant now.
    assert table[8][1] == a2_shape_quarters(0, 8, is_table=True)
    assert plain[8][1] == a2_shape_quarters(0, 8, is_table=False)

    source.close()


def test_a2_unique_tiles_rejects_negative_tolerance() -> None:
    """A negative tolerance is rejected before any composition runs."""

    source = Image.new("RGBA", (96, 96), (90, 90, 90, 255))

    with pytest.raises(ValueError):
        list(a2_unique_tiles(source, tolerance=-1))

    source.close()