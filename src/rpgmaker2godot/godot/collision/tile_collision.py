from rpgmaker2godot.model.tile_collision import TileCollision


def has_collision(collision: TileCollision | None) -> bool:
    """Return whether a tile contains collision information.

    A tile without collision information must remain collision-free
    in the generated Godot TileSet.

    This helper intentionally does not decide how directional
    collision is represented geometrically. That responsibility
    belongs to the Godot export layer implemented in this milestone.
    """

    return collision is not None