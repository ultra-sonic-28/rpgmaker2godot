from pathlib import Path

from rpgmaker2godot.godot.model import (
    GodotAtlasMapping,
    GodotAtlasSource,
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


def make_godot_atlas_source() -> GodotAtlasSource:
    return GodotAtlasSource(
        texture_path=Path("Inside.png"),
        texture_width=96,
        texture_height=96,
        tile_width=48,
        tile_height=48,
        tiles=(
            GodotAtlasTile(
                ref=TileRef("Inside", 0, index=0),
                source_x=0,
                source_y=0,
                atlas_x=0,
                atlas_y=0,
                cell=GodotAtlasCell(
                    column=0,
                    row=0,
                ),
                width=48,
                height=48,
            ),
            GodotAtlasTile(
                ref=TileRef("Inside", 1, index=0),
                source_x=48,
                source_y=0,
                atlas_x=48,
                atlas_y=0,
                cell=GodotAtlasCell(
                    column=1,
                    row=0,
                ),
                width=48,
                height=48,
            ),
            GodotAtlasTile(
                ref=TileRef("Inside", 2, index=0),
                source_x=0,
                source_y=48,
                atlas_x=0,
                atlas_y=48,
                cell=GodotAtlasCell(
                    column=0,
                    row=1,
                ),
                width=48,
                height=48,
            ),
            GodotAtlasTile(
                ref=TileRef("Inside", 3, index=0),
                source_x=48,
                source_y=48,
                atlas_x=48,
                atlas_y=48,
                cell=GodotAtlasCell(
                    column=1,
                    row=1,
                ),
                width=48,
                height=48,
            ),
        ),
    )