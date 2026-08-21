from dataclasses import dataclass


@dataclass(frozen=True)
class TileCollision:
    """Collision information for one tile.

    A TileCollision describes which of the four sides of a tile
    block passage.

    This model deliberately contains no Godot-specific concept.
    It represents the semantic result of RPG Maker's directional
    passage flags and can therefore be tested independently from
    the Godot exporter.

    Attributes:
        block_down:
            True when movement through the bottom side of the tile
            must be blocked.

        block_left:
            True when movement through the left side of the tile
            must be blocked.

        block_right:
            True when movement through the right side of the tile
            must be blocked.

        block_up:
            True when movement through the top side of the tile
            must be blocked.
    """

    block_down: bool
    block_left: bool
    block_right: bool
    block_up: bool