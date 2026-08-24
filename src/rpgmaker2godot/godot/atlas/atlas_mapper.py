from rpgmaker2godot.model.tile import Tile

from ...atlas.models import Atlas
from ..model import (
    GodotAtlasMapping,
    GodotAtlasTile,
)


class GodotAtlasMapper:
    """Map the internal atlas representation to Godot atlas coordinates."""

    def map(self, atlas: Atlas) -> GodotAtlasMapping:
        if atlas.width % atlas.tile_width != 0:
            raise ValueError(
                "Atlas width must be a multiple of tile width: "
                f"{atlas.width} is not divisible by {atlas.tile_width}"
            )

        if atlas.height % atlas.tile_height != 0:
            raise ValueError(
                "Atlas height must be a multiple of tile height: "
                f"{atlas.height} is not divisible by {atlas.tile_height}"
            )
        
        tiles = tuple(
            GodotAtlasTile(
                ref=placement.tile,
                source_x=placement.source_x,
                source_y=placement.source_y,
                atlas_x=placement.atlas_x,
                atlas_y=placement.atlas_y,
                cell=None,
                width=placement.width,
                height=placement.height,

                # Propagate the collision information carried
                # by the converted Tile to the Godot atlas model.
                collision=placement.collision,
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