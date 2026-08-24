from enum import Enum


class SheetType(Enum):
    """RPG Maker tileset sheet types handled by the current converter."""

    A5 = "A5"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

    @property
    def order(self) -> int:
        """Canonical ordering used when stacking sheets into an atlas.

        RPG Maker draws A5 first, followed by B, C, D and E.
        """

        return _SHEET_ORDER[self]


_SHEET_ORDER: dict[SheetType, int] = {
    SheetType.A5: 0,
    SheetType.B: 1,
    SheetType.C: 2,
    SheetType.D: 3,
    SheetType.E: 4,
}