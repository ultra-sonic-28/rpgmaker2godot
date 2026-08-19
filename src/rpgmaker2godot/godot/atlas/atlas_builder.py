from rpgmaker2godot.godot.model import GodotAtlasSource
from rpgmaker2godot.godot.resource import GodotAtlasSourceResource

from rpgmaker2godot.godot.model import GodotAtlasTileResource

class GodotAtlasSourceBuilder:
    """Build a serializable Godot TileSetAtlasSource resource."""

    def build(
        self,
        source: GodotAtlasSource,
        *,
        resource_id: str,
        texture_resource_id: str,
    ) -> GodotAtlasSourceResource:
        tiles = tuple(
            GodotAtlasTileResource(
            column=tile.cell.column,
            row=tile.cell.row,
        )
            for tile in source.tiles
        )

        return GodotAtlasSourceResource(
            resource_id=resource_id,
            texture_resource_id=texture_resource_id,
            tile_width=source.tile_width,
            tile_height=source.tile_height,
            tiles=tiles,
        )