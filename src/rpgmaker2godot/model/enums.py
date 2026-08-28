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


_SHEET_ORDER: dict[SheetType, int] = {
    SheetType.A4: 0,
    SheetType.A5: 1,
    SheetType.B: 2,
    SheetType.C: 3,
    SheetType.D: 4,
    SheetType.E: 5,
}