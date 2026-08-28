from dataclasses import dataclass

from ..model import Tile
from .model import TileProperties, TilesetFlags

_PASS_DOWN = 0x0001
_PASS_LEFT = 0x0002
_PASS_RIGHT = 0x0004
_PASS_UP = 0x0008

_STAR = 0x0010
_LADDER = 0x0020
_BUSH = 0x0040
_COUNTER = 0x0080
_DAMAGE_FLOOR = 0x0100

TERRAIN_TAG_MASK = 0xF000
TERRAIN_TAG_SHIFT = 12


def decode_tile_flags(flags: int) -> TileProperties:
    """Decode one RPG Maker MV/MZ tile flag.

    RPG Maker stores several independent properties in a 16-bit
    integer. The four lowest bits represent blocked directions:
    a set bit means that passage in that direction is forbidden.

    Our model exposes the inverse semantic:

        RPG Maker bit set   -> passage blocked
        can_pass_*          -> False

    The remaining properties are represented by individual bits,
    while the terrain tag occupies the high nibble.

    This function deliberately does not decode vehicle restrictions
    yet because they are outside the current A5/B/C/D/E collision
    scope.

    Args:
        flags: Raw value from the `flags` array in Tilesets.json.

    Returns:
        Semantic properties for the tile.

    Raises:
        ValueError: If flags is outside the unsigned 16-bit range.
    """

    if not 0 <= flags <= 0xFFFF:
        raise ValueError(
            f"Tile flags must be between 0 and 65535, got {flags!r}."
        )

    return TileProperties(
        can_pass_down=not bool(flags & _PASS_DOWN),
        can_pass_left=not bool(flags & _PASS_LEFT),
        can_pass_right=not bool(flags & _PASS_RIGHT),
        can_pass_up=not bool(flags & _PASS_UP),

        is_star=bool(flags & _STAR),
        is_ladder=bool(flags & _LADDER),
        is_bush=bool(flags & _BUSH),
        is_counter=bool(flags & _COUNTER),
        is_damage_floor=bool(flags & _DAMAGE_FLOOR),

        terrain_tag=(
            (flags & TERRAIN_TAG_MASK)
            >> TERRAIN_TAG_SHIFT
        ),
    )