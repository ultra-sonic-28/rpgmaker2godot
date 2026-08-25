from ...atlas.models import Atlas
from ..model import (
    GodotAtlasMapping,
    GodotAtlasTile,
)
from ..tileset.collision import tile_collision_to_godot


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

                # Transform the semantic RPG Maker collision into
                # Godot geometry. This is the explicit frontier
                # between the two collision models.
                collision=tile_collision_to_godot(
                    placement.collision,
                    width=placement.width,
                    height=placement.height,
                    # Diagnostic coordinates of the tile inside the
                    # resulting Godot tileset. The authoritative cell
                    # assignment still happens in GodotTileSetBuilder.
                    cell=(
                        placement.atlas_x // atlas.tile_width,
                        placement.atlas_y // atlas.tile_height,
                    ),
                ),
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