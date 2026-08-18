from dataclasses import dataclass

from ..model import TileRef


@dataclass(frozen=True)
class GodotAtlasTile:
    ref: TileRef

    atlas_x: int
    atlas_y: int

    width: int
    height: int


@dataclass(frozen=True)
class GodotAtlasMapping:
    tile_width: int
    tile_height: int

    width: int
    height: int

    tiles: tuple[GodotAtlasTile, ...]