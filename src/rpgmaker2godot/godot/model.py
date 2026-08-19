from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class GodotAtlasSource:
    texture_path: Path

    tile_width: int
    tile_height: int

    texture_width: int
    texture_height: int

    tiles: tuple[GodotAtlasTile, ...]


@dataclass(frozen=True)
class GodotTileSet:
    tile_width: int
    tile_height: int

    atlas_sources: tuple[GodotAtlasSource, ...]


@dataclass(frozen=True)
class GodotAtlasCell:
    column: int
    row: int


@dataclass(frozen=True)
class GodotAtlasTile:
    ref: TileRef

    source_x: int
    source_y: int

    atlas_x: int
    atlas_y: int

    cell: GodotAtlasCell

    width: int
    height: int


@dataclass(frozen=True)
class GodotAtlasTileResource:
    """Serialized representation of a TileSetAtlasSource cell."""
    
    column: int
    row: int


@dataclass(frozen=True)
class GodotAtlasSourceResource:
    resource_id: str
    texture_resource_id: str

    tile_width: int
    tile_height: int

    tiles: tuple[GodotAtlasTileResource, ...]