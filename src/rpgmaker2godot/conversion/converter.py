from collections import defaultdict
from collections.abc import Iterator

from rpgmaker2godot.analysis.models import AnalysisResult, SheetInfo
from rpgmaker2godot.model import (
    ConversionResult,
    Sheet,
    Tile,
    Tileset,
)


class SimpleConverter:
    """Convert an AnalysisResult into the internal representation.

    The simple converter currently handles regular 48x48 RPG Maker
    sheets only. It does not decode autotiles or manipulate image data.
    """

    def convert(self, analysis: AnalysisResult) -> ConversionResult:
        grouped_sheets: dict[str, list[SheetInfo]] = defaultdict(list)

        for sheet_info in analysis.sheets:
            grouped_sheets[sheet_info.prefix].append(sheet_info)

        tilesets: list[Tileset] = []

        for name, sheet_infos in sorted(grouped_sheets.items()):
            sheets = tuple(
                self._convert_sheet(sheet_info)
                for sheet_info in sorted(
                    sheet_infos,
                    key=lambda sheet: self._sheet_order(sheet),
                )
            )

            tilesets.append(
                Tileset(
                    name=name,
                    sheets=sheets,
                )
            )

        return ConversionResult(
            tilesets=tuple(tilesets),
        )

    def _convert_sheet(self, sheet_info: SheetInfo) -> Sheet:
        tiles = tuple(
            self._create_tile(
                index=index,
                column=column,
                row=row,
                tile_width=sheet_info.tile_width,
                tile_height=sheet_info.tile_height,
            )
            for index, (row, column) in enumerate(
                self._tile_coordinates(
                    columns=sheet_info.columns,
                    rows=sheet_info.rows,
                )
            )
        )

        return Sheet(
            sheet_type=sheet_info.sheet_type,
            source_path=sheet_info.path,
            width=sheet_info.width,
            height=sheet_info.height,
            tile_width=sheet_info.tile_width,
            tile_height=sheet_info.tile_height,
            columns=sheet_info.columns,
            rows=sheet_info.rows,
            tiles=tiles,
        )

    @staticmethod
    def _tile_coordinates(
        columns: int,
        rows: int,
    ) -> Iterator[tuple[int, int]]:
        for row in range(rows):
            for column in range(columns):
                yield row, column

    @staticmethod
    def _create_tile(
        index: int,
        column: int,
        row: int,
        tile_width: int,
        tile_height: int,
    ) -> Tile:
        return Tile(
            index=index,
            column=column,
            row=row,
            x=column * tile_width,
            y=row * tile_height,
            width=tile_width,
            height=tile_height,
        )

    @staticmethod
    def _sheet_order(sheet_info: SheetInfo) -> int:
        order = {
            "A5": 0,
            "B": 1,
            "C": 2,
            "D": 3,
            "E": 4,
        }

        return order[sheet_info.sheet_type.value]