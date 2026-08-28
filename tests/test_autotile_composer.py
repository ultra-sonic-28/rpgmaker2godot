import pytest
from PIL import Image

from rpgmaker2godot.tileset.autotile import (
    FLOOR_AUTOTILE_TABLE,
    QUARTER_SIZE,
    TILE_SIZE,
    WALL_AUTOTILE_TABLE,
    compose_autotile,
    unfold_floor_autotile,
    unfold_wall_autotile,
)
from rpgmaker2godot.tileset.autotile.a4 import a4_source_region


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