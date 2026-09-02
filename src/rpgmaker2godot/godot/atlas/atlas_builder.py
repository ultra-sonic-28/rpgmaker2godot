from rpgmaker2godot.godot.model import (
    GodotAtlasSource,
    GodotAtlasTileResource,
    GodotTerrainPlan,
)
from rpgmaker2godot.godot.resource.resource import GodotAtlasSourceResource


class GodotAtlasSourceBuilder:
    """Build a serializable Godot TileSetAtlasSource resource."""

    def build(
        self,
        source: GodotAtlasSource,
        *,
        resource_id: str,
        texture_resource_id: str,
        terrain_plan: GodotTerrainPlan | None = None,
    ) -> GodotAtlasSourceResource:
        tiles: list[GodotAtlasTileResource] = []

        for tile in source.tiles:
            if tile.cell is None:
                raise ValueError(
                    f"Tile {tile.ref} has no Godot atlas cell assigned."
                )

            tiles.append(
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
                    collision=tile.collision,
                    terrain=(
                        terrain_plan.tile_terrains.get(tile.ref)
                        if terrain_plan is not None
                        else None
                    ),
                )
            )

        return GodotAtlasSourceResource(
            resource_id=resource_id,
            texture_resource_id=texture_resource_id,
            tile_width=source.tile_width,
            tile_height=source.tile_height,
            tiles=tuple(tiles),
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