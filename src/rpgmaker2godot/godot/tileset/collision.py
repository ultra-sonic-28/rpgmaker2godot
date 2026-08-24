from dataclasses import dataclass


@dataclass(frozen=True)
class GodotTileCollision:
    """Godot representation of a tile collision polygon.

    The polygon coordinates are expressed in pixels relative to the
    tile's local origin.

    For the initial export milestone, a collision is represented by
    one polygon covering the complete tile. The interpretation of
    RPG Maker's directional passability flags is intentionally kept
    outside this class.

    This class only represents geometry that is ready to be serialized
    into Godot's TileData.
    """

    points: tuple[tuple[float, float], ...]