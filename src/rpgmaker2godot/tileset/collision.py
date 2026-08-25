from rpgmaker2godot.model.tile_collision import TileCollision
from rpgmaker2godot.tileset.model import TileProperties
from ..utils.log import get_logger

logger = get_logger("tileset.collision")


def tile_properties_to_collision(
    properties: TileProperties,
    *,
    tile_id: int | None = None,
    coord: tuple[int, int] | None = None,
) -> TileCollision:
    """Convert RPG Maker tile properties into collision semantics.

    RPG Maker exposes directional passage as positive permissions:

        can_pass_* = True
            -> passage is allowed

        can_pass_* = False
            -> passage is blocked

    TileCollision intentionally uses the opposite representation:

        block_* = True
            -> this side blocks movement

        block_* = False
            -> this side does not block movement

    The conversion is therefore a direct boolean inversion.

    Other RPG Maker properties such as ``is_ladder``, ``is_bush``,
    ``is_counter``, ``is_damage_floor`` and ``terrain_tag`` are
    intentionally ignored here.

    They describe gameplay or rendering semantics rather than
    directional collision and will be handled by later stages.

    Args:
        properties:
            Semantic RPG Maker properties associated with the tile.
        tile_id: Diagnostic only — global RPG Maker Tile ID, included
            in the debug log when provided.
        coord: Diagnostic only — (column, row) of the tile inside its
            RPG Maker sheet, included in the debug log when provided.

    Returns:
        The directional collision representation of the tile.
    """

    result = TileCollision(
        block_down=not properties.can_pass_down,
        block_left=not properties.can_pass_left,
        block_right=not properties.can_pass_right,
        block_up=not properties.can_pass_up,
    )

    identifier_suffix = ""

    if tile_id is not None:
        identifier_suffix = f" tile_id={tile_id}"

    coordinate_suffix = ""

    if coord is not None:
        coordinate_suffix = f" coord=({coord[0]}, {coord[1]})"

    logger.debug(
        "properties -> collision%s%s: %s -> %s",
        identifier_suffix,
        coordinate_suffix,
        properties,
        result,
    )

    return result