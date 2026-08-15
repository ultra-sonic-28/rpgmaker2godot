from dataclasses import dataclass

from .sheet import Sheet


@dataclass(frozen=True)
class Tileset:
    name: str
    sheets: tuple[Sheet, ...]


@dataclass(frozen=True)
class ConversionResult:
    tilesets: tuple[Tileset, ...]