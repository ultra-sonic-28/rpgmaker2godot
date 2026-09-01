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
class CharacterSheetInfo:
    """One detected character spritesheet file.

    The frame size is derived from the image size: the width holds
    exactly three frames and the height exactly nine rows (the fixed
    character layout — see
    :mod:`rpgmaker2godot.character.layout`).
    """

    path: Path
    width: int
    height: int
    frame_width: int
    frame_height: int
    columns: int
    rows: int


@dataclass(frozen=True)
class CharacterAnalysisResult:
    """Analysis result for a directory of character spritesheets."""

    input_directory: Path
    sheets: tuple[CharacterSheetInfo, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisResult:
    input_directory: Path
    version: RPGMakerVersion
    tile_width: int
    tile_height: int
    sheets: tuple[SheetInfo, ...]
    warnings: tuple[str, ...]