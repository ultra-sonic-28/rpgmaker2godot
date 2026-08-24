from pathlib import Path

from rpgmaker2godot.atlas.models import Atlas
from rpgmaker2godot.godot.model import (
    GodotAtlasMapping,
    GodotAtlasSource,
    GodotAtlasTile,
    GodotAtlasCell,
)
from rpgmaker2godot.model import SheetType, TileRef
from rpgmaker2godot.model.sheet import Sheet
from rpgmaker2godot.model.tile import Tile
from rpgmaker2godot.model.tileset import ConversionResult, Tileset
from tests.helpers.atlas import make_tile_ref


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
                ref=TileRef("Inside", SheetType.B, index=0),
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
                ref=TileRef("Inside", SheetType.C, index=0),
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
                ref=TileRef("Inside", SheetType.D, index=0),
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
                ref=TileRef("Inside", SheetType.E, index=0),
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


def make_atlas(
    *,
    width: int = 96,
    height: int = 96,
    tile_width: int = 48,
    tile_height: int = 48,
) -> Atlas:
    return Atlas(
        width=width,
        height=height,
        tile_width=tile_width,
        tile_height=tile_height,
        placements=(),
    )


def make_large_godot_atlas_mapping() -> GodotAtlasMapping:
    tile_size = 48

    return GodotAtlasMapping(
        tile_width=tile_size,
        tile_height=tile_size,
        width=4 * tile_size,
        height=6 * tile_size,
        tiles=(
            GodotAtlasTile(
                ref=make_tile_ref(index=0),
                source_x=0,
                source_y=0,
                atlas_x=0,
                atlas_y=0,
                cell=None,
                width=2 * tile_size,
                height=1 * tile_size,
            ),
            GodotAtlasTile(
                ref=make_tile_ref(index=1),
                source_x=0,
                source_y=0,
                atlas_x=2 * tile_size,
                atlas_y=0,
                cell=None,
                width=1 * tile_size,
                height=2 * tile_size,
            ),
            GodotAtlasTile(
                ref=make_tile_ref(index=2),
                source_x=0,
                source_y=0,
                atlas_x=0,
                atlas_y=2 * tile_size,
                cell=None,
                width=2 * tile_size,
                height=3 * tile_size,
            ),
        ),
    )


def make_multi_cell_conversion(
    source_path: Path,
) -> ConversionResult:
    tile_size = 48

    tiles = (
        Tile(
            ref=make_tile_ref(index=0),
            column=0,
            row=0,
            x=0,
            y=0,
            width=2 * tile_size,
            height=1 * tile_size,
        ),
        Tile(
            ref=make_tile_ref(index=1),
            column=2,
            row=0,
            x=2 * tile_size,
            y=0,
            width=1 * tile_size,
            height=2 * tile_size,
        ),
        Tile(
            ref=make_tile_ref(index=2),
            column=0,
            row=2,
            x=0,
            y=2 * tile_size,
            width=2 * tile_size,
            height=3 * tile_size,
        ),
    )

    sheet = Sheet(
        sheet_type=SheetType.A5,
        source_path=source_path,
        width=4 * tile_size,
        height=6 * tile_size,
        tile_width=tile_size,
        tile_height=tile_size,
        columns=4,
        rows=6,
        tiles=tiles,
    )

    tileset = Tileset(
        name="Inside",
        sheets=(sheet,),
    )

    return ConversionResult(
        tilesets=(tileset,),
    )