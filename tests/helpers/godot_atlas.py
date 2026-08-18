from pathlib import Path

from rpgmaker2godot.godot.model import (
    GodotAtlasMapping,
    GodotAtlasTile,
    GodotAtlasCell,
)
from rpgmaker2godot.model import SheetType, TileRef


def make_mapping_with_tile(
    *,
    atlas_x: int,
    atlas_y: int,
) -> GodotAtlasMapping:
    tile = GodotAtlasTile(
        ref=TileRef(
            tileset="Inside",
            sheet_type=SheetType.B,
            index=0,
        ),
        source_x=0,
        source_y=0,
        atlas_x=atlas_x,
        atlas_y=atlas_y,
        cell=GodotAtlasCell(
            column=0,
            row=0,
        ),
        width=48,
        height=48,
    )

    return GodotAtlasMapping(
        width=96,
        height=96,
        tile_width=48,
        tile_height=48,
        tiles=(tile,),
    )