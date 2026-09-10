from enum import Enum


class SheetType(Enum):
    """RPG Maker tileset sheet types handled by the current converter."""

    A1 = "A1"
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

        RPG Maker draws the ``A`` sheets first (the A1 animated water,
        the A2 ground, the building walls from A3, the interior walls
        from A4, then the flat A5 ground), followed by the B, C, D and
        E object sheets. The A sheets must always appear *under* the
        B-E overlays, hence A1-A4 are stacked before A5.
        """

        return _SHEET_ORDER[self]

    @property
    def is_autotile(self) -> bool:
        """Whether this sheet belongs to the autotile family (A1-A4).

        Autotile sheets hold raw material that the engine composes from
        four 24x24 quarters per tile. The converter merges them into
        their own ``<prefix>_Autotile`` output tileset, separate from
        the normal sheets. A1, A2, A3 and A4 are handled by the
        converter and the merge process picks them up automatically.
        """

        return self in _AUTOTILE_SHEET_TYPES


_AUTOTILE_SHEET_TYPES: frozenset[SheetType] = frozenset(
    # The autotile sheet types handled by the converter.
    {SheetType.A1, SheetType.A2, SheetType.A3, SheetType.A4},
)

_SHEET_ORDER: dict[SheetType, int] = {
    SheetType.A1: 0,
    SheetType.A2: 1,
    SheetType.A3: 2,
    SheetType.A4: 3,
    SheetType.A5: 4,
    SheetType.B: 5,
    SheetType.C: 6,
    SheetType.D: 7,
    SheetType.E: 8,
}