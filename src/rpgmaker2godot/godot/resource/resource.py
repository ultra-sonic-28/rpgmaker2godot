from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GodotExtResource:
    resource_id: str
    resource_type: str
    path: str


@dataclass(frozen=True)
class GodotAtlasSourceResource:
    resource_id: str

    texture_resource_id: str

    tile_width: int
    tile_height: int

    tiles: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class GodotTileSetResource:
    tile_width: int
    tile_height: int

    texture: GodotExtResource
    atlas_source: GodotAtlasSourceResource