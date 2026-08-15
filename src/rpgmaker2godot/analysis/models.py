from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rpgmaker2godot.model import SheetType

class RPGMakerVersion(Enum):
    UNKNOWN = "unknown"
    MV = "mv"
    MZ = "mz"


@dataclass(frozen=True)
class SheetInfo:
    sheet_type: SheetType
    path: Path
    prefix: str
    width: int
    height: int
    tile_width: int
    tile_height: int
    columns: int
    rows: int


@dataclass(frozen=True)
class AnalysisResult:
    input_directory: Path
    version: RPGMakerVersion
    tile_width: int
    tile_height: int
    sheets: tuple[SheetInfo, ...]
    warnings: tuple[str, ...]