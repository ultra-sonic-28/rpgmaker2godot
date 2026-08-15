from dataclasses import dataclass
from pathlib import Path

from .enums import SheetType
from .tile import Tile


@dataclass(frozen=True)
class Sheet:
    sheet_type: SheetType
    source_path: Path
    width: int
    height: int
    tile_width: int
    tile_height: int
    columns: int
    rows: int
    tiles: tuple[Tile, ...]