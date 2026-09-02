from typing import TypeGuard

from rpgmaker2godot.model.tile_collision import TileCollision


def has_collision(collision: TileCollision | None) -> TypeGuard[TileCollision]:
    """Return whether a tile actually blocks movement.

    A tile without collision information — or whose directional flags
    are all open (RPG Maker raw flags ``0x0000``) — must remain
    collision-free in the generated Godot TileSet.

    This helper intentionally does not decide how directional
    collision is represented geometrically. That responsibility
    belongs to the Godot export layer implemented in this milestone.
    """

    if collision is None:
        return False

    return (
        collision.block_down
        or collision.block_left
        or collision.block_right
        or collision.block_up
    )