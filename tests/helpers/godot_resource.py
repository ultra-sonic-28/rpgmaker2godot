from rpgmaker2godot.godot.resource import (
    GodotAtlasSourceResource,
    GodotExtResource,
    GodotTileSetResource,
)
from rpgmaker2godot.godot.resource_serializer import (
    GodotResourceSerializer,
)
from rpgmaker2godot.godot.model import (
    GodotAtlasTileResource, 
)

def make_resource() -> GodotTileSetResource:
    texture = GodotExtResource(
        resource_id="1_texture",
        resource_type="Texture2D",
        path="res://Inside.png",
    )

    atlas = GodotAtlasSourceResource(
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
        tile_width=48,
        tile_height=48,
        tiles=(
            GodotAtlasTileResource(column=0, row=0),
            GodotAtlasTileResource(column=1, row=0),
            GodotAtlasTileResource(column=0, row=1),
            GodotAtlasTileResource(column=1, row=1),
    ),
    )

    return GodotTileSetResource(
        tile_width=48,
        tile_height=48,
        texture=texture,
        atlas_source=atlas,
    )
