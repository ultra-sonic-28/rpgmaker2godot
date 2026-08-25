from dataclasses import dataclass

from rpgmaker2godot.godot.collision.tile_collision import has_collision
from rpgmaker2godot.model.tile_collision import TileCollision


@dataclass(frozen=True)
class GodotTileCollision:
    """Collision geometry associated with one Godot atlas tile.

    The polygon is expressed in tile-local pixel coordinates,
    relative to the CENTER of the tile — matching Godot's own
    convention in the TileSet editor (a 48x48 tile therefore spans
    from (-24, -24) to (24, 24)).

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
    the complete tile area, centered on the tile origin:
    from (-width/2, -height/2) to (+width/2, +height/2).

    The directional passability flags carried by TileCollision
    are deliberately not interpreted into partial geometry yet; that
    translation belongs to a dedicated collision milestone.
    """

    if not has_collision(collision):
        return None

    half_width = width / 2.0
    half_height = height / 2.0

    return GodotTileCollision(
        points=(
            (-half_width, -half_height),
            (half_width, -half_height),
            (half_width, half_height),
            (-half_width, half_height),
        ),
    )