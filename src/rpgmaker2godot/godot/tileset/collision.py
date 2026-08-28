from dataclasses import dataclass

from rpgmaker2godot.godot.collision.tile_collision import has_collision
from rpgmaker2godot.model.tile_collision import TileCollision

from ...utils.log import get_logger

logger = get_logger("godot.tileset.collision")

# Thickness in pixels of the wall bands generated along every
# blocked side of a tile.
_WALL_THICKNESS = 8.0


@dataclass(frozen=True)
class GodotTileCollision:
    """Collision geometry associated with one Godot atlas tile.

    Each polygon is expressed in tile-local pixel coordinates,
    relative to the CENTER of the tile — matching Godot's own
    convention in the TileSet editor (a 48x48 tile therefore spans
    from (-24, -24) to (24, 24)).

    A tile carries one polygon per blocked side: thin wall bands
    (see ``_WALL_THICKNESS``) plastered against the corresponding
    edge. Blocking opposite sides therefore produces two separate
    bands. Blocking every side makes the tile fully solid: a
    single rectangle covering the whole tile replaces the bands.
    """

    polygons: tuple[tuple[tuple[float, float], ...], ...]

    def __post_init__(self) -> None:
        if len(self.polygons) < 1:
            raise ValueError(
                "At least one collision polygon is required."
            )

        for polygon in self.polygons:
            if len(polygon) < 3:
                raise ValueError(
                    "A collision polygon must contain at least "
                    "three points."
                )

            for point in polygon:
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
    cell: tuple[int, int] | None = None,
) -> GodotTileCollision | None:
    """Transform semantic RPG Maker collision into Godot geometry.

    This function is the explicit frontier between the two collision
    models:

        TileCollision (RPG Maker semantics)
            │  tile_collision_to_godot()
            ▼
        GodotTileCollision (Godot geometry)

    A tile without collision information must stay collision-free.

    Geometry is built as thin wall bands plastered against every
    blocked side, expressed around the tile center (Godot convention):

        block_down   -> bottom band    block_up    -> top band
        block_left   -> left band      block_right -> right band

    Each band is _WALL_THICKNESS pixels thick and spans the full
    length of its edge. Blocking several sides therefore produces
    several polygons (left AND right give two separate vertical
    walls).

    When every side is blocked, the tile is fully solid: the four
    bands are replaced by a single rectangle covering the whole
    tile area.

    Args:
        collision: Semantic directional collision of the tile, or None.
        width: Tile width in pixels.
        height: Tile height in pixels.
        cell: Diagnostic only — coordinates of the tile in the
            resulting Godot tileset, included in the debug log when
            provided. The authoritative cell assignment happens later,
            in GodotTileSetBuilder.

    Returns:
        The Godot collision polygon, or None when the tile blocks
        nothing.
    """

    if not has_collision(collision):
        return None

    half_width = width / 2.0
    half_height = height / 2.0

    polygons: list[tuple[tuple[float, float], ...]] = []

    if (
        collision.block_down
        and collision.block_left
        and collision.block_right
        and collision.block_up
    ):
        # Every side is blocked: the whole tile is solid. One
        # rectangle covering the full tile area replaces the
        # individual wall bands.
        polygons.append((
            (-half_width, -half_height),
            (half_width, -half_height),
            (half_width, half_height),
            (-half_width, half_height),
        ))
    else:
        # Tiles smaller than the wall thickness get proportionally
        # thinner walls instead of overlapping bands.
        thickness = min(_WALL_THICKNESS, half_width, half_height)

        if collision.block_down:
            polygons.append((
                (-half_width, half_height - thickness),
                (half_width, half_height - thickness),
                (half_width, half_height),
                (-half_width, half_height),
            ))

        if collision.block_up:
            polygons.append((
                (-half_width, -half_height),
                (half_width, -half_height),
                (half_width, -half_height + thickness),
                (-half_width, -half_height + thickness),
            ))

        if collision.block_left:
            polygons.append((
                (-half_width, -half_height),
                (-half_width + thickness, -half_height),
                (-half_width + thickness, half_height),
                (-half_width, half_height),
            ))

        if collision.block_right:
            polygons.append((
                (half_width - thickness, -half_height),
                (half_width, -half_height),
                (half_width, half_height),
                (half_width - thickness, half_height),
            ))

    polygon = GodotTileCollision(polygons=tuple(polygons))

    coordinate_suffix = ""

    if cell is not None:
        coordinate_suffix = f" coord=({cell[0]}, {cell[1]})"

    logger.debug(
        "collision -> geometry %dx%d px%s: %s -> %s",
        width,
        height,
        coordinate_suffix,
        collision,
        polygon.polygons,
    )

    return polygon