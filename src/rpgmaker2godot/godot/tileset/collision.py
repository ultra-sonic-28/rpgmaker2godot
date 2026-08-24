from dataclasses import dataclass

from rpgmaker2godot.godot.collision.tile_collision import has_collision
from rpgmaker2godot.model.tile_collision import TileCollision


@dataclass(frozen=True)
class GodotTileCollision:
    """Collision geometry associated with one Godot atlas tile.

    The polygon is expressed in tile-local pixel coordinates.

    The origin (0, 0) corresponds to the top-left corner of the tile.
    Coordinates therefore use the same coordinate system as Godot's
    TileSet collision polygons.

    Keeping the geometry independent from the .tres serialization format
    allows the resource writer to remain responsible solely for translating
    our internal representation into Godot's textual resource syntax.
    """

    points: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if len(self.points) < 3:
            raise ValueError(
                "A collision polygon must contain at least "
                "three points."
            )

        for point in self.points:
            if len(point) != 2:
                raise ValueError(
                    "A collision point must contain exactly "
                    "two coordinates."
                )


def tile_collision_to_godot(
    collision: TileCollision | None,
    *,
    width: int,
    height: int,
) -> GodotTileCollision | None:
    """Transform semantic RPG Maker collision into Godot geometry.

    This function is the explicit frontier between the two collision
    models:

        TileCollision (RPG Maker semantics)
            │  tile_collision_to_godot()
            ▼
        GodotTileCollision (Godot geometry)

    A tile without collision information must stay collision-free.

    At this stage, any collision is represented by a rectangle covering
    the complete tile area (width x height pixels, origin at the top-left
    corner). The directional passability flags carried by TileCollision
    are deliberately not interpreted into partial geometry yet; that
    translation belongs to a dedicated collision milestone.
    """

    if not has_collision(collision):
        return None

    return GodotTileCollision(
        points=(
            (0.0, 0.0),
            (float(width), 0.0),
            (float(width), float(height)),
            (0.0, float(height)),
        ),
    )