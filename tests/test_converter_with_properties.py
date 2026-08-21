from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

from rpgmaker2godot.analysis.models import (
    AnalysisResult,
    RPGMakerVersion,
    SheetInfo,
)
from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.conversion import SimpleConverter
from rpgmaker2godot.model.tile import Tile
from rpgmaker2godot.tileset.model import TileProperties


def make_sheet_info(
    *,
    prefix: str = "Inside",
    sheet_type: SheetType = SheetType.A5,
    width: int = 96,
    height: int = 96,
    tile_width: int = 48,
    tile_height: int = 48,
) -> SheetInfo:
    return SheetInfo(
        prefix=prefix,
        sheet_type=sheet_type,
        path=Path("Inside_A5.png"),
        width=width,
        height=height,
        tile_width=tile_width,
        tile_height=tile_height,
        columns=width // tile_width,
        rows=height // tile_height,
    )


def make_analysis(
    *sheet_infos: SheetInfo,
) -> AnalysisResult:
    return AnalysisResult(
        input_directory=Path("."),
        version=RPGMakerVersion.MV,
        tile_width=48,
        tile_height=48,
        sheets=tuple(sheet_infos),
        warnings=(),
    )


def test_converter_leaves_tile_properties_empty_without_resolver() -> None:
    analysis = make_analysis(
        make_sheet_info(),
    )

    result = SimpleConverter().convert(analysis)

    tiles = result.tilesets[0].sheets[0].tiles

    assert len(tiles) == 4

    for tile in tiles:
        assert tile.properties is None


def test_converter_resolves_tile_properties() -> None:
    properties = TileProperties(
        can_pass_down=False,
        can_pass_left=True,
        can_pass_right=False,
        can_pass_up=True,
        is_star=False,
        is_ladder=True,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=3,
    )

    resolver = Mock()
    resolver.resolve.return_value = properties

    analysis = make_analysis(
        make_sheet_info(),
    )

    result = SimpleConverter(
        tile_properties_resolver=resolver,
    ).convert(analysis)

    tiles = result.tilesets[0].sheets[0].tiles

    assert len(tiles) == 4

    for tile in tiles:
        assert tile.properties == properties

    assert resolver.resolve.call_count == 4


def test_converter_resolves_properties_using_created_tile() -> None:
    properties = TileProperties(
        can_pass_down=False,
        can_pass_left=True,
        can_pass_right=True,
        can_pass_up=True,
        is_star=False,
        is_ladder=False,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=0,
    )

    resolved_tiles: list[Tile] = []

    def resolve(tile: Tile) -> TileProperties:
        resolved_tiles.append(tile)
        return properties

    resolver = Mock()
    resolver.resolve.side_effect = resolve

    analysis = make_analysis(
        make_sheet_info(),
    )

    result = SimpleConverter(
        tile_properties_resolver=resolver,
    ).convert(analysis)

    tiles = result.tilesets[0].sheets[0].tiles

    assert resolved_tiles == [
        Tile(
            ref=tile.ref,
            column=tile.column,
            row=tile.row,
            x=tile.x,
            y=tile.y,
            width=tile.width,
            height=tile.height,
        )
        for tile in tiles
    ]

    assert all(
        tile.properties == properties
        for tile in tiles
    )


def test_converter_preserves_tile_geometry_when_resolving_properties() -> None:
    properties = TileProperties(
        can_pass_down=False,
        can_pass_left=False,
        can_pass_right=False,
        can_pass_up=False,
        is_star=True,
        is_ladder=False,
        is_bush=False,
        is_counter=False,
        is_damage_floor=False,
        terrain_tag=7,
    )

    resolver = Mock()
    resolver.resolve.return_value = properties

    analysis = make_analysis(
        make_sheet_info(
            width=96,
            height=48,
        ),
    )

    result = SimpleConverter(
        tile_properties_resolver=resolver,
    ).convert(analysis)

    tiles = result.tilesets[0].sheets[0].tiles

    assert tiles == (
        replace(
            tiles[0],
            properties=properties,
        ),
        replace(
            tiles[1],
            properties=properties,
        ),
    )

    assert tiles[0].column == 0
    assert tiles[0].row == 0
    assert tiles[0].x == 0
    assert tiles[0].y == 0
    assert tiles[0].width == 48
    assert tiles[0].height == 48

    assert tiles[1].column == 1
    assert tiles[1].row == 0
    assert tiles[1].x == 48
    assert tiles[1].y == 0


def test_converter_assigns_resolved_properties_to_each_tile() -> None:
    properties_by_index = {
        0: TileProperties(
            can_pass_down=True,
            can_pass_left=True,
            can_pass_right=True,
            can_pass_up=True,
            is_star=False,
            is_ladder=False,
            is_bush=False,
            is_counter=False,
            is_damage_floor=False,
            terrain_tag=0,
        ),
        1: TileProperties(
            can_pass_down=False,
            can_pass_left=True,
            can_pass_right=True,
            can_pass_up=True,
            is_star=False,
            is_ladder=True,
            is_bush=False,
            is_counter=False,
            is_damage_floor=False,
            terrain_tag=2,
        ),
    }

    def resolve(tile):
        return properties_by_index[tile.ref.index]

    resolver = Mock()
    resolver.resolve.side_effect = resolve

    analysis = make_analysis(
        make_sheet_info(
            width=96,
            height=48,
        ),
    )

    result = SimpleConverter(
        tile_properties_resolver=resolver,
    ).convert(analysis)

    tiles = result.tilesets[0].sheets[0].tiles

    assert tiles[0].properties == properties_by_index[0]
    assert tiles[1].properties == properties_by_index[1]