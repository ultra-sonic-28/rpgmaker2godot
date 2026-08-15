from dataclasses import dataclass


@dataclass(frozen=True)
class Tile:
    index: int
    column: int
    row: int
    x: int
    y: int
    width: int
    height: int