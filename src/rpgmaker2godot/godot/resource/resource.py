from dataclasses import dataclass

from ..model import GodotAtlasTileResource, GodotTerrainSet


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

    tiles: tuple[GodotAtlasTileResource, ...]


@dataclass(frozen=True)
class GodotTileSetResource:
    tile_width: int
    tile_height: int

    texture: GodotExtResource
    atlas_source: GodotAtlasSourceResource

    has_physics_layer: bool = False

    terrain_sets: tuple[GodotTerrainSet, ...] = ()