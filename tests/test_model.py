from pathlib import Path

from rpgmaker2godot.model import (
    ConversionResult,
    Sheet,
    SheetType,
    Tile,
    Tileset,
)

import pytest

def test_tile() -> None:
    tile = Tile(
        index=17,
        column=1,
        row=1,
        x=48,
        y=48,
        width=48,
        height=48,
    )

    assert tile.index == 17
    assert tile.column == 1
    assert tile.row == 1
    assert tile.x == 48
    assert tile.y == 48
    assert tile.width == 48
    assert tile.height == 48


def test_sheet() -> None:
    tiles = (
        Tile(
            index=0,
            column=0,
            row=0,
            x=0,
            y=0,
            width=48,
            height=48,
        ),
        Tile(
            index=1,
            column=1,
            row=0,
            x=48,
            y=0,
            width=48,
            height=48,
        ),
    )

    sheet = Sheet(
        sheet_type=SheetType.B,
        source_path=Path("Inside_B.png"),
        width=768,
        height=768,
        tile_width=48,
        tile_height=48,
        columns=16,
        rows=16,
        tiles=tiles,
    )

    assert sheet.sheet_type == SheetType.B
    assert sheet.columns == 16
    assert sheet.rows == 16
    assert len(sheet.tiles) == 2


def test_tileset() -> None:
    sheet = Sheet(
        sheet_type=SheetType.B,
        source_path=Path("Inside_B.png"),
        width=768,
        height=768,
        tile_width=48,
        tile_height=48,
        columns=16,
        rows=16,
        tiles=(),
    )

    tileset = Tileset(
        name="Inside",
        sheets=(sheet,),
    )

    assert tileset.name == "Inside"
    assert len(tileset.sheets) == 1
    assert tileset.sheets[0].sheet_type == SheetType.B


def test_conversion_result() -> None:
    tileset = Tileset(
        name="Inside",
        sheets=(),
    )

    result = ConversionResult(
        tilesets=(tileset,),
    )

    assert len(result.tilesets) == 1
    assert result.tilesets[0].name == "Inside"

def test_tile_is_immutable() -> None:
    tile = Tile(
        index=0,
        column=0,
        row=0,
        x=0,
        y=0,
        width=48,
        height=48,
    )

    with pytest.raises(AttributeError):
        tile.x = 48

def test_sheet_is_immutable() -> None:
    sheet = Sheet(
        sheet_type=SheetType.B,
        source_path=Path("B.png"),
        width=768,
        height=768,
        tile_width=48,
        tile_height=48,
        columns=16,
        rows=16,
        tiles=(),
    )

    with pytest.raises(AttributeError):
        sheet.columns = 8