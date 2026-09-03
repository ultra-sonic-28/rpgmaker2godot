from enum import Enum


class SheetType(Enum):
    """RPG Maker tileset sheet types handled by the current converter."""

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

        RPG Maker draws the ``A`` sheets first (the building walls from
        A3, the interior walls from A4, then the flat A5 ground),
        followed by the B, C, D and E object sheets. The A sheets must
        always appear *under* the B-E overlays, hence A3 and A4 are
        stacked before A5.
        """

        return _SHEET_ORDER[self]

    @property
    def is_autotile(self) -> bool:
        """Whether this sheet belongs to the autotile family (A1-A4).

        Autotile sheets hold raw material that the engine composes from
        four 24x24 quarters per tile. The converter merges them into
        their own ``<prefix>_Autotile`` output tileset, separate from
        the normal sheets. A3 and A4 are currently handled by the
        converter; A1-A2 are added to :data:`_AUTOTILE_SHEET_TYPES`
        when their unfolding is implemented, and the merge process
        picks them up automatically.
        """

        return self in _AUTOTILE_SHEET_TYPES


_AUTOTILE_SHEET_TYPES: frozenset[SheetType] = frozenset(
    # A1 and A2 join this set when the converter learns to unfold
    # them; until then A3 and A4 are the autotile sheet types.
    {SheetType.A3, SheetType.A4},
)

_SHEET_ORDER: dict[SheetType, int] = {
    SheetType.A3: 0,
    SheetType.A4: 1,
    SheetType.A5: 2,
    SheetType.B: 3,
    SheetType.C: 4,
    SheetType.D: 5,
    SheetType.E: 6,
}