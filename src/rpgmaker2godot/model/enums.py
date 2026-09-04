from enum import Enum


class SheetType(Enum):
    """RPG Maker tileset sheet types handled by the current converter."""

    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

    @property
    def order(self) -> int:
        """Canonical ordering used when stacking sheets into an atlas.

        RPG Maker draws the ``A`` sheets first (the A2 ground, the
        building walls from A3, the interior walls from A4, then the
        flat A5 ground), followed by the B, C, D and E object sheets.
        The A sheets must always appear *under* the B-E overlays, hence
        A2, A3 and A4 are stacked before A5.
        """

        return _SHEET_ORDER[self]

    @property
    def is_autotile(self) -> bool:
        """Whether this sheet belongs to the autotile family (A1-A4).

        Autotile sheets hold raw material that the engine composes from
        four 24x24 quarters per tile. The converter merges them into
        their own ``<prefix>_Autotile`` output tileset, separate from
        the normal sheets. A2, A3 and A4 are currently handled by the
        converter; A1 joins :data:`_AUTOTILE_SHEET_TYPES` when its
        unfolding is implemented, and the merge process picks it up
        automatically.
        """

        return self in _AUTOTILE_SHEET_TYPES


_AUTOTILE_SHEET_TYPES: frozenset[SheetType] = frozenset(
    # A1 joins this set when the converter learns to unfold it; until
    # then A2, A3 and A4 are the autotile sheet types.
    {SheetType.A2, SheetType.A3, SheetType.A4},
)

_SHEET_ORDER: dict[SheetType, int] = {
    SheetType.A2: 0,
    SheetType.A3: 1,
    SheetType.A4: 2,
    SheetType.A5: 3,
    SheetType.B: 4,
    SheetType.C: 5,
    SheetType.D: 6,
    SheetType.E: 7,
}