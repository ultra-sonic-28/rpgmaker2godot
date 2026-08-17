from dataclasses import dataclass
from pathlib import Path

from rpgmaker2godot.model import TileRef


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


@dataclass(frozen=True)
class Atlas:
    width: int
    height: int
    tile_width: int
    tile_height: int
    placements: tuple[AtlasPlacement, ...]