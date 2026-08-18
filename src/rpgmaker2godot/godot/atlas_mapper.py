from ..atlas.models import Atlas
from .model import (
    GodotAtlasMapping,
    GodotAtlasTile,
)


class GodotAtlasMapper:
    """Map the internal atlas representation to Godot atlas coordinates."""

    def map(self, atlas: Atlas) -> GodotAtlasMapping:
        tiles = tuple(
            GodotAtlasTile(
                ref=placement.tile,
                atlas_x=placement.atlas_x,
                atlas_y=placement.atlas_y,
                width=placement.width,
                height=placement.height,
            )
            for placement in atlas.placements
        )

        return GodotAtlasMapping(
            tile_width=atlas.tile_width,
            tile_height=atlas.tile_height,
            width=atlas.width,
            height=atlas.height,
            tiles=tiles,
        )