from dataclasses import dataclass
from pathlib import Path

from rpgmaker2godot.model import TileRef
from rpgmaker2godot.model.tile_collision import TileCollision


@dataclass(frozen=True)
class AtlasQuarter:
    """One 24px-wide source piece pasted into the atlas tile.

    Used by the "unfolded autotile" placements (A2/A3/A4): those tiles
    are not a single rectangular crop of the source sheet, they are
    composed of quarter pieces. ``source_x``/``source_y`` locate the
    piece in the source sheet and ``dest_x``/``dest_y`` place it inside
    the atlas tile (atlas_x + dest_x, atlas_y + dest_y). A piece is
    24px wide and usually 24px tall; the A2 table rendering also emits
    12px-tall halves.
    """

    source_x: int
    source_y: int
    dest_x: int
    dest_y: int
    width: int
    height: int


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

    # When non-empty, the placement is assembled from these source
    # quarters instead of the single ``source_x``/``source_y`` crop.
    quarters: tuple[AtlasQuarter, ...] = ()


@dataclass(frozen=True)
class Atlas:
    width: int
    height: int
    tile_width: int
    tile_height: int
    placements: tuple[AtlasPlacement, ...]