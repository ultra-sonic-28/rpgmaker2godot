from dataclasses import dataclass
from pathlib import Path

from rpgmaker2godot.godot.tileset.collision import GodotTileCollision

from ..model import TileRef


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

    # Assigned later by GodotTileSetBuilder; None until then (the
    # mapper only knows atlas pixel coordinates, not grid cells).
    cell: GodotAtlasCell | None

    width: int
    height: int

    collision: GodotTileCollision | None = None


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
class GodotTerrain:
    """One terrain of a terrain set (a paintable "material")."""

    name: str
    color: tuple[float, float, float]


@dataclass(frozen=True)
class GodotTerrainSet:
    """A terrain set: a matching mode plus its terrains."""

    mode: int
    terrains: tuple[GodotTerrain, ...]


@dataclass(frozen=True)
class GodotTileTerrain:
    """Terrain assignment of one atlas tile."""

    set_index: int
    terrain_index: int
    # (peering_bit_name, terrain_index) pairs; only connected directions
    # are listed — the others stay -1 (Godot's default).
    peering_bits: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class GodotTerrainPlan:
    """Terrain metadata attached to a generated TileSet."""

    terrain_sets: tuple[GodotTerrainSet, ...]
    tile_terrains: dict[TileRef, GodotTileTerrain]


@dataclass(frozen=True)
class GodotAtlasTileResource:
    """Serialized representation of a TileSetAtlasSource cell."""

    column: int
    row: int
    width: int = 1
    height: int = 1

    collision: GodotTileCollision | None = None

    terrain: GodotTileTerrain | None = None

    def __post_init__(self) -> None:
        if self.column < 0:
            raise ValueError(
                "Atlas tile column must be >= 0."
            )

        if self.row < 0:
            raise ValueError(
                "Atlas tile row must be >= 0."
            )

        if self.width <= 0:
            raise ValueError(
                "Atlas tile width must be > 0."
            )

        if self.height <= 0:
            raise ValueError(
                "Atlas tile height must be > 0."
            )
