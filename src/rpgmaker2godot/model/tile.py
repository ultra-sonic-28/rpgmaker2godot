from dataclasses import dataclass

from rpgmaker2godot.model.tile_collision import TileCollision
from rpgmaker2godot.tileset.model import TileProperties

from .enums import SheetType


@dataclass(frozen=True)
class TileRef:
    tileset: str
    sheet_type: SheetType
    index: int


@dataclass(frozen=True)
class Tile:
    """Representation of one RPG Maker tileset tile.

    A Tile contains the information needed by the conversion pipeline
    to identify a source tile and preserve its geometry.

    ``properties`` contains the semantic RPG Maker properties decoded
    from Tilesets.json.

    ``collision`` contains the directional collision semantics derived
    from those properties.

    Keeping both values on the Tile is intentional:

    * TileProperties represents RPG Maker semantics.
    * TileCollision represents the collision model used by the
      conversion pipeline.

    The collision model is kept separate from TileProperties so that
    later stages do not need to understand RPG Maker's raw flag
    representation.

    ``collision`` is optional because Tiles can still be created by
    parts of the pipeline that do not have access to Tilesets.json.
    This preserves the existing behaviour of the converter when no
    TilePropertiesResolver is configured.
    """
    
    ref: TileRef
    column: int
    row: int
    x: int
    y: int
    width: int
    height: int
    properties: TileProperties | None = None
    collision: TileCollision | None = None


__all__ = [
    "Tile",
    "TileRef",
]