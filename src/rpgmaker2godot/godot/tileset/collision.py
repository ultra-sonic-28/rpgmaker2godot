from dataclasses import dataclass


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