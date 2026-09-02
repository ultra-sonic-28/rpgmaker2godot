from enum import Enum


class SheetType(Enum):
    """RPG Maker tileset sheet types handled by the current converter."""

    A4 = "A4"
    A5 = "A5"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

    @property
    def order(self) -> int:
        """Canonical ordering used when stacking sheets into an atlas.

        RPG Maker draws the ``A`` sheets first (walls from A4, then the
        flat A5 ground), followed by the B, C, D and E object sheets.
        The A sheets must always appear *under* the B-E overlays, hence
        A4 is stacked before A5.
        """

        return _SHEET_ORDER[self]

    @property
    def is_autotile(self) -> bool:
        """Whether this sheet belongs to the autotile family (A1-A4).

        Autotile sheets hold raw material that the engine composes from
        four 24x24 quarters per tile. The converter merges them into
        their own ``<prefix>_Autotile`` output tileset, separate from
        the normal sheets. Only A4 is currently handled by the
        converter; A1-A3 are added to :data:`_AUTOTILE_SHEET_TYPES`
        when their unfolding is implemented, and the merge process
        picks them up automatically.
        """

        return self in _AUTOTILE_SHEET_TYPES


_AUTOTILE_SHEET_TYPES: frozenset[SheetType] = frozenset(
    # A1, A2 and A3 join this set when the converter learns to unfold
    # them; until then only A4 is an autotile sheet type.
    {SheetType.A4},
)

_SHEET_ORDER: dict[SheetType, int] = {
    SheetType.A4: 0,
    SheetType.A5: 1,
    SheetType.B: 2,
    SheetType.C: 3,
    SheetType.D: 4,
    SheetType.E: 5,
}