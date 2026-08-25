from rpgmaker2godot.tileset.flags import decode_tile_flags
from rpgmaker2godot.tileset.tile_id import tile_to_tile_id

from ..model import Tile
from ..utils.log import get_logger
from rpgmaker2godot.tileset.model import TileProperties, TilesetFlags

logger = get_logger("tileset.resolver")


class TilePropertiesResolver:
    """Resolve RPG Maker properties for converter tiles."""

    def __init__(
        self,
        tilesets: dict[str, TilesetFlags],
    ) -> None:
        self._tilesets = tilesets

    def resolve(
        self,
        tile: Tile,
    ) -> TileProperties:
        """Resolve the properties associated with a Tile."""

        tileset_name = tile.ref.tileset

        try:
            tileset = self._tilesets[tileset_name]
        except KeyError as exc:
            raise ValueError(
                f"Unknown RPG Maker tileset: {tileset_name!r}"
            ) from exc

        tile_id = tile_to_tile_id(tile)

        raw_flags = tileset.get(tile_id)

        logger.debug(
            "resolve %s tile_id=%d coord=(%d, %d) raw_flags=0x%04X",
            tileset_name,
            tile_id,
            tile.column,
            tile.row,
            raw_flags,
        )

        return decode_tile_flags(raw_flags)