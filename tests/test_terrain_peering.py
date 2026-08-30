"""The hardcoded peering tables match the constraint-solver solution."""

from rpgmaker2godot.tileset.autotile.peering import (
    FLOOR_SHAPE_CONNECTIONS,
    PEERING_DIRECTIONS,
    WALL_SHAPE_CONNECTIONS,
    floor_shape_peering,
    wall_shape_peering,
)
from rpgmaker2godot.tileset.autotile.shapes import (
    FLOOR_AUTOTILE_TABLE,
    WALL_AUTOTILE_TABLE,
)

STATES = tuple(
    (side_a, diagonal, side_b)
    for side_a in (0, 1)
    for side_b in (0, 1)
    for diagonal in (0, 1)
    if diagonal <= side_a and diagonal <= side_b
)

CORNERS = ("TL", "TR", "BL", "BR")


def _solve_shape_connections(table):
    """Solve the per-slot local states of one autotile table.

    Returns every solution as a list of per-shape 8-tuples
    (left, top, right, bottom, tl, tr, bl, br).
    """

    slot_ids = {}
    per_shape = []

    for quarters in table:
        row = []

        for corner, (qx, qy) in zip(CORNERS, quarters):
            key = (corner, qx, qy)

            if key not in slot_ids:
                slot_ids[key] = len(slot_ids)

            row.append(slot_ids[key])

        per_shape.append(row)

    assign = [None] * len(slot_ids)
    seen = {}
    duplicated = [False]
    solutions = []
    last_shape = len(table) - 1

    order = []

    for shape in (0, last_shape, *range(len(table))):
        for slot in per_shape[shape]:
            if slot not in order:
                order.append(slot)

    def cfg_of(shape):
        tl, tr, bl, br = (assign[i] for i in per_shape[shape])

        return (
            tl[0] & bl[0],
            tl[2] & tr[0],
            tr[2] & br[0],
            bl[2] & br[2],
            tl[1],
            tr[1],
            bl[1],
            br[1],
        )

    def check(shape):
        row = per_shape[shape]

        if any(assign[i] is None for i in row):
            return True

        cfg = cfg_of(shape)
        left, top, right, bottom, tl, tr, bl, br = cfg

        if shape == 0 and cfg != (1, 1, 1, 1, 1, 1, 1, 1):
            return False

        if shape == last_shape and cfg != (0, 0, 0, 0, 0, 0, 0, 0):
            return False

        if tl and not (left and top):
            return False

        if tr and not (top and right):
            return False

        if bl and not (left and bottom):
            return False

        if br and not (bottom and right):
            return False

        tl_q, tr_q, bl_q, br_q = (assign[i] for i in row)

        if tl_q[0] != bl_q[0] or tl_q[2] != tr_q[0]:
            return False

        if tr_q[2] != br_q[0] or bl_q[2] != br_q[2]:
            return False

        if cfg in seen:
            if duplicated[0]:
                return False

            duplicated[0] = True
        else:
            seen[cfg] = shape

        return True

    def uncheck(shape):
        row = per_shape[shape]

        if any(assign[i] is None for i in row):
            return

        cfg = cfg_of(shape)

        if seen.get(cfg) == shape:
            del seen[cfg]
        else:
            duplicated[0] = False

    def backtrack(pos):
        if pos == len(order):
            solutions.append(
                tuple(cfg_of(s) for s in range(len(table))),
            )

            return True

        slot = order[pos]

        for state in STATES:
            assign[slot] = state

            touched = [
                s for s in range(len(table)) if slot in per_shape[s]
            ]

            ok = True

            for shape in touched:
                if not check(shape):
                    ok = False
                    break

            if ok and backtrack(pos + 1):
                return True

            for shape in touched:
                uncheck(shape)

            assign[slot] = None

        return False

    backtrack(0)

    return solutions


def test_floor_connections_match_the_unique_constraint_solution() -> None:
    solutions = _solve_shape_connections(FLOOR_AUTOTILE_TABLE)

    assert len(solutions) == 1

    solution = solutions[0]

    assert tuple(
        tuple(int(flag) for flag in connections)
        for connections in FLOOR_SHAPE_CONNECTIONS
    ) == solution


def test_floor_coverage_is_the_classic_blob_set() -> None:
    configs = set(FLOOR_SHAPE_CONNECTIONS)

    assert len(configs) == 47

    assert FLOOR_SHAPE_CONNECTIONS[0] == (True,) * 8
    assert FLOOR_SHAPE_CONNECTIONS[46] == (False,) * 8
    assert FLOOR_SHAPE_CONNECTIONS[47] == (False,) * 8

    for connections in configs:
        left, top, right, bottom, tl, tr, bl, br = connections

        assert not tl or (left and top)
        assert not tr or (top and right)
        assert not bl or (left and bottom)
        assert not br or (bottom and right)


def test_wall_connections_derive_from_the_quarter_table() -> None:
    """Wall sides: a side connects when both of its quarters are clear.

    The wall table picks each quarter independently from a border
    column/row or the interior: west border quarters sit in column 0,
    east in column 3, north in row 0 and south in row 3. A side of the
    composed tile therefore connects exactly when neither of its two
    quarters carries that border.
    """

    for shape, quarters in enumerate(WALL_AUTOTILE_TABLE):
        tl, tr, bl, br = quarters

        expected = (
            tl[0] != 0 and bl[0] != 0,   # left
            tl[1] != 0 and tr[1] != 0,   # top
            tr[0] != 3 and br[0] != 3,   # right
            bl[1] != 3 and br[1] != 3,   # bottom
        )

        assert WALL_SHAPE_CONNECTIONS[shape] == expected, shape

    # The 16 shapes cover every side combination exactly once.
    assert len(set(WALL_SHAPE_CONNECTIONS)) == 16


def test_floor_shape_peering_exposes_godot_directions() -> None:
    peering = dict(floor_shape_peering(0))

    assert tuple(peering.keys()) == PEERING_DIRECTIONS
    assert all(peering.values())

    assert not any(dict(floor_shape_peering(47)).values())


def test_wall_shape_peering_exposes_sides_only() -> None:
    peering = dict(wall_shape_peering(1))

    assert set(peering) == {
        "right_side",
        "bottom_side",
        "left_side",
        "top_side",
    }

    assert peering["left_side"] is False
    assert peering["top_side"] is True
    assert peering["right_side"] is True
    assert peering["bottom_side"] is True