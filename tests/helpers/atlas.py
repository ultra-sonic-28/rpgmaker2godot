from pathlib import Path

from rpgmaker2godot.model import (
    Sheet,
    SheetType,
    Tile,
    TileRef,
    Tileset,
)


def make_sheet(
    sheet_type: SheetType = SheetType.B,
    width: int = 96,
    height: int = 96,
    tile_width: int = 48,
    tile_height: int = 48,
    tileset: str = "Inside",
    source_directory: Path | None = None,
) -> Sheet:
    columns = width // tile_width
    rows = height // tile_height

    filename = f"{tileset}_{sheet_type.value}.png"

    source_path = (
        source_directory / filename
        if source_directory is not None
        else Path(filename)
    )

    tiles = tuple(
        Tile(
            ref=TileRef(
                tileset=tileset,
                sheet_type=sheet_type,
                index=index,
            ),
            column=index % columns,
            row=index // columns,
            x=(index % columns) * tile_width,
            y=(index // columns) * tile_height,
            width=tile_width,
            height=tile_height,
        )
        for index in range(columns * rows)
    )

    return Sheet(
        sheet_type=sheet_type,
        source_path=source_path,
        width=width,
        height=height,
        tile_width=tile_width,
        tile_height=tile_height,
        columns=columns,
        rows=rows,
        tiles=tiles,
    )


def make_tileset(
    sheet: Sheet | None = None,
    name: str = "Inside",
) -> Tileset:
    if sheet is None:
        sheet = make_sheet()

    return Tileset(
        name=name,
        sheets=(sheet,),
    )


def make_tileset_with_sheets(
    *sheets: Sheet,
    name: str = "Inside",
) -> Tileset:
    return Tileset(
        name=name,
        sheets=tuple(sheets),
    )


def make_tile_ref(
    *,
    index: int,
    tileset: str = "Inside",
    sheet_type: SheetType = SheetType.A5,
) -> TileRef:
    return TileRef(
        tileset=tileset,
        sheet_type=sheet_type,
        index=index,
    )