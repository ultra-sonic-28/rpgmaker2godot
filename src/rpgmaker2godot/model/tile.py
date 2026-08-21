from dataclasses import dataclass

from rpgmaker2godot.tileset.model import TileProperties

from .enums import SheetType


@dataclass(frozen=True)
class TileRef:
    tileset: str
    sheet_type: SheetType
    index: int


@dataclass(frozen=True)
class Tile:
    """A tile discovered in an RPG Maker tileset sheet.

    `properties` is populated during conversion from RPG Maker's
    Tilesets.json flags. It is optional at the model level so that
    low-level sheet detection remains independent from Tilesets.json.
    """
    
    ref: TileRef
    column: int
    row: int
    x: int
    y: int
    width: int
    height: int
    properties: TileProperties | None = None


__all__ = [
    "Tile",
    "TileRef",
]