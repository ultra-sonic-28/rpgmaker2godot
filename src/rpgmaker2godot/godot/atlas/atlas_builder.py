from rpgmaker2godot.godot.model import GodotAtlasSource
from rpgmaker2godot.godot.resource.resource import GodotAtlasSourceResource

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
                width=self._to_cell_dimension(
                    tile.width,
                    source.tile_width,
                ),
                height=self._to_cell_dimension(
                    tile.height,
                    source.tile_height,
                ),
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


    @staticmethod
    def _to_cell_dimension(
        pixels: int,
        tile_size: int,
    ) -> int:
        if pixels <= 0:
            raise ValueError(
                "Tile dimension must be positive."
            )

        if pixels % tile_size != 0:
            raise ValueError(
                "Tile dimension must be aligned "
                "to the atlas tile size."
            )

        return pixels // tile_size