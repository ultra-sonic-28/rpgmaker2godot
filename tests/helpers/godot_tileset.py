from pathlib import Path

from rpgmaker2godot.godot.model import (
    GodotAtlasCell,
    GodotAtlasSource,
    GodotAtlasSourceResource,
    GodotAtlasTile,
    GodotAtlasTileResource,
    GodotTileSet,
)
from rpgmaker2godot.godot.resource.resource import GodotExtResource, GodotTileSetResource
from rpgmaker2godot.model import SheetType, TileRef


def make_godot_tileset() -> GodotTileSet:
    tiles = tuple(
        GodotAtlasTile(
            ref=TileRef(
                tileset="Inside",
                sheet_type=SheetType.B,
                index=index,
            ),
            source_x=(index % 2) * 48,
            source_y=(index // 2) * 48,
            atlas_x=(index % 2) * 48,
            atlas_y=(index // 2) * 48,
            cell=GodotAtlasCell(
                column=index % 2,
                row=index // 2,
            ),
            width=48,
            height=48,
        )
        for index in range(4)
    )

    source = GodotAtlasSource(
        texture_path=Path("Inside.png"),
        texture_width=96,
        texture_height=96,
        tile_width=48,
        tile_height=48,
        tiles=tiles,
    )

    return GodotTileSet(
        tile_width=48,
        tile_height=48,
        atlas_sources=(source,),
    )


def make_godot_tileset_with_multiple_sources() -> GodotTileSet:
    first = make_godot_tileset().atlas_sources[0]

    second_tiles = tuple(
        GodotAtlasTile(
            ref=TileRef(
                tileset="Inside",
                sheet_type=SheetType.C,
                index=index,
            ),
            source_x=(index % 2) * 48,
            source_y=(index // 2) * 48,
            atlas_x=(index % 2) * 48,
            atlas_y=(index // 2) * 48,
            cell=GodotAtlasCell(
                column=index % 2,
                row=index // 2,
            ),
            width=48,
            height=48,
        )
        for index in range(4)
    )

    second = GodotAtlasSource(
        texture_path=Path("Inside_2.png"),
        texture_width=96,
        texture_height=96,
        tile_width=48,
        tile_height=48,
        tiles=second_tiles,
    )

    return GodotTileSet(
        tile_width=48,
        tile_height=48,
        atlas_sources=(
            first,
            second,
        ),
    )


def make_godot_tileset_resource(
    *,
    tiles: tuple[GodotAtlasTileResource, ...] | None = None,
) -> GodotTileSetResource:
    if tiles is None:
        tiles = (
            GodotAtlasTileResource(
                column=0,
                row=0,
            ),
            GodotAtlasTileResource(
                column=1,
                row=0,
            ),
            GodotAtlasTileResource(
                column=0,
                row=1,
            ),
            GodotAtlasTileResource(
                column=1,
                row=1,
            ),
        )

    texture = GodotExtResource(
        resource_id="1_texture",
        resource_type="Texture2D",
        path="res://Inside.png",
    )

    atlas_source = GodotAtlasSourceResource(
        resource_id="TileSetAtlasSource_1",
        texture_resource_id="1_texture",
        tile_width=48,
        tile_height=48,
        tiles=tiles,
    )

    return GodotTileSetResource(
        tile_width=48,
        tile_height=48,
        texture=texture,
        atlas_source=atlas_source,
    )