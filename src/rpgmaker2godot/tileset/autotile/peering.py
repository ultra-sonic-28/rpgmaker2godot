"""Shape → peering-bit correspondence for the autotile tables.

Godot's terrain system selects tiles by matching per-tile *peering bits*
(expected terrain on each side/corner) against the neighbours painted by
the user. Reproducing RPG Maker's ``_addAutotile`` behaviour therefore
requires knowing, for every shape of the engine tables, which sides and
corners the composed tile visually connects.

This correspondence is derived from ``FLOOR_AUTOTILE_TABLE`` and
``WALL_AUTOTILE_TABLE`` themselves: each table slot carries a local
state ``(side_a, diagonal, side_b)`` shared by every shape using it,
constrained by:

* the anchors — shape 0 is fully surrounded, shape 47 is isolated;
* well-formed edges — the two quarters of a composed tile edge agree;
* blob validity — a connected corner implies both adjacent sides;
* coverage — the 48 floor shapes yield exactly 47 distinct
  configurations (the classic blob set) plus one duplicated isolated
  variant (shapes 46/47), and the 16 wall shapes yield all 16
  side-only combinations. The A3 building autotiles (roofs and walls)
  and the A4 Wall Sides compose from the wall table, so they all share
  ``WALL_SHAPE_CONNECTIONS``.

``tests/test_terrain_peering.py`` re-runs the constraint solver and
asserts the hardcoded tables below, so the mapping cannot drift.
"""

# Godot peering-bit names, in Godot's own enumeration order
# (TileSet.TerrainPeeringBit).
PEERING_DIRECTIONS = (
    "right_side",
    "bottom_right_corner",
    "bottom_side",
    "bottom_left_corner",
    "left_side",
    "top_left_corner",
    "top_side",
    "top_right_corner",
)

# Per floor shape (Wall Top, 48 shapes): which of the tile's sides and
# corners visually connect, in (left, top, right, bottom, top_left,
# top_right, bottom_left, bottom_right) order. Solved from
# FLOOR_AUTOTILE_TABLE — see the module docstring.
FLOOR_SHAPE_CONNECTIONS: tuple[tuple[bool, ...], ...] = (
    (True, True, True, True, True, True, True, True),    # 0
    (True, True, True, True, False, True, True, True),   # 1
    (True, True, True, True, True, False, True, True),   # 2
    (True, True, True, True, False, False, True, True),  # 3
    (True, True, True, True, True, True, True, False),   # 4
    (True, True, True, True, False, True, True, False),  # 5
    (True, True, True, True, True, False, True, False),  # 6
    (True, True, True, True, False, False, True, False),  # 7
    (True, True, True, True, True, True, False, True),   # 8
    (True, True, True, True, False, True, False, True),  # 9
    (True, True, True, True, True, False, False, True),  # 10
    (True, True, True, True, False, False, False, True),  # 11
    (True, True, True, True, True, True, False, False),  # 12
    (True, True, True, True, False, True, False, False),  # 13
    (True, True, True, True, True, False, False, False),  # 14
    (True, True, True, True, False, False, False, False),  # 15
    (False, True, True, True, False, True, False, True),  # 16
    (False, True, True, True, False, False, False, True),  # 17
    (False, True, True, True, False, True, False, False),  # 18
    (False, True, True, True, False, False, False, False),  # 19
    (True, False, True, True, False, False, True, True),   # 20
    (True, False, True, True, False, False, True, False),  # 21
    (True, False, True, True, False, False, False, True),  # 22
    (True, False, True, True, False, False, False, False),  # 23
    (True, True, False, True, True, False, True, False),   # 24
    (True, True, False, True, True, False, False, False),  # 25
    (True, True, False, True, False, False, True, False),  # 26
    (True, True, False, True, False, False, False, False),  # 27
    (True, True, True, False, True, True, False, False),   # 28
    (True, True, True, False, False, True, False, False),  # 29
    (True, True, True, False, True, False, False, False),  # 30
    (True, True, True, False, False, False, False, False),  # 31
    (False, True, False, True, False, False, False, False),  # 32
    (True, False, True, False, False, False, False, False),  # 33
    (False, False, True, True, False, False, False, True),  # 34
    (False, False, True, True, False, False, False, False),  # 35
    (True, False, False, True, False, False, True, False),  # 36
    (True, False, False, True, False, False, False, False),  # 37
    (True, True, False, False, True, False, False, False),  # 38
    (True, True, False, False, False, False, False, False),  # 39
    (False, True, True, False, False, True, False, False),  # 40
    (False, True, True, False, False, False, False, False),  # 41
    (False, False, False, True, False, False, False, False),  # 42
    (False, False, True, False, False, False, False, False),  # 43
    (False, True, False, False, False, False, False, False),  # 44
    (True, False, False, False, False, False, False, False),  # 45
    (False, False, False, False, False, False, False, False),  # 46
    (False, False, False, False, False, False, False, False),  # 47
)

# Per wall shape (Wall Side, 16 shapes): the four sides, in (left, top,
# right, bottom) order. The wall table cycles over 16 shapes covering
# every side combination; shape s borders exactly the sides cleared in
# its bitmask (1=left, 2=top, 4=right, 8=bottom).
WALL_SHAPE_CONNECTIONS: tuple[tuple[bool, ...], ...] = tuple(
    (
        not bool(shape & 1),
        not bool(shape & 2),
        not bool(shape & 4),
        not bool(shape & 8),
    )
    for shape in range(16)
)


def floor_shape_peering(
    shape: int,
) -> tuple[tuple[str, bool], ...]:
    """Return the ``(peering_bit_name, connected)`` pairs of a Wall Top."""

    left, top, right, bottom, tl, tr, bl, br = FLOOR_SHAPE_CONNECTIONS[shape]

    return (
        ("right_side", right),
        ("bottom_right_corner", br),
        ("bottom_side", bottom),
        ("bottom_left_corner", bl),
        ("left_side", left),
        ("top_left_corner", tl),
        ("top_side", top),
        ("top_right_corner", tr),
    )


def wall_shape_peering(
    shape: int,
) -> tuple[tuple[str, bool], ...]:
    """Return the ``(peering_bit_name, connected)`` pairs of a Wall Side."""

    left, top, right, bottom = WALL_SHAPE_CONNECTIONS[shape]

    return (
        ("right_side", right),
        ("bottom_side", bottom),
        ("left_side", left),
        ("top_side", top),
    )


__all__ = [
    "FLOOR_SHAPE_CONNECTIONS",
    "PEERING_DIRECTIONS",
    "WALL_SHAPE_CONNECTIONS",
    "floor_shape_peering",
    "wall_shape_peering",
]