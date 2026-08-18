from pathlib import Path

from .model import (
    GodotAtlasCell,
    GodotAtlasMapping,
    GodotAtlasSource,
    GodotAtlasTile,
    GodotTileSet,
)


class GodotTileSetBuilder:
    """Build a Godot-oriented TileSet representation."""

    def build(
        self,
        mapping: GodotAtlasMapping,
        texture_path: Path,
    ) -> GodotTileSet:

        tiles = tuple(
            GodotAtlasTile(
                ref=tile.ref,
                source_x=tile.source_x,
                source_y=tile.source_y,
                atlas_x=tile.atlas_x,
                atlas_y=tile.atlas_y,
                cell=GodotAtlasCell(
                    column=tile.atlas_x // mapping.tile_width,
                    row=tile.atlas_y // mapping.tile_height,
                ),
                width=tile.width,
                height=tile.height,
            )
            for tile in mapping.tiles
        )

        source = GodotAtlasSource(
            texture_path=texture_path,
            tile_width=mapping.tile_width,
            tile_height=mapping.tile_height,
            texture_width=mapping.width,
            texture_height=mapping.height,
            tiles=tiles,
        )

        return GodotTileSet(
            tile_width=mapping.tile_width,
            tile_height=mapping.tile_height,
            atlas_sources=(source,),
        )