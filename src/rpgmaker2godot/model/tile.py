from dataclasses import dataclass

from .enums import SheetType


@dataclass(frozen=True)
class TileRef:
    tileset: str
    sheet_type: SheetType
    index: int


@dataclass(frozen=True)
class Tile:
    ref: TileRef
    column: int
    row: int
    x: int
    y: int
    width: int
    height: int


__all__ = [
    "Tile",
    "TileRef",
]