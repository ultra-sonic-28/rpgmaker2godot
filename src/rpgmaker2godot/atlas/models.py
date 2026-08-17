from dataclasses import dataclass

from rpgmaker2godot.model import TileRef


@dataclass(frozen=True)
class AtlasPlacement:
    tile: TileRef
    x: int
    y: int


@dataclass(frozen=True)
class Atlas:
    width: int
    height: int
    tile_width: int
    tile_height: int
    placements: tuple[AtlasPlacement, ...]