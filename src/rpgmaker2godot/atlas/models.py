from dataclasses import dataclass
from pathlib import Path

from rpgmaker2godot.model import TileRef
from rpgmaker2godot.model.tile_collision import TileCollision


@dataclass(frozen=True)
class AtlasPlacement:
    tile: TileRef

    source_path: Path
    source_x: int
    source_y: int

    atlas_x: int
    atlas_y: int

    width: int
    height: int

    collision: TileCollision | None = None


@dataclass(frozen=True)
class Atlas:
    width: int
    height: int
    tile_width: int
    tile_height: int
    placements: tuple[AtlasPlacement, ...]