from collections import defaultdict
from collections.abc import Iterator
from dataclasses import replace

from rpgmaker2godot.analysis.models import AnalysisResult, SheetInfo
from rpgmaker2godot.model import (
    ConversionResult,
    Sheet,
    Tile,
    Tileset,
    TileRef,
)
from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.tileset.collision import tile_properties_to_collision
from rpgmaker2godot.tileset.resolver import TilePropertiesResolver


class SimpleConverter:
    """Convert an AnalysisResult into the internal representation."""

    def __init__(
        self,
        *,
        tile_properties_resolver: TilePropertiesResolver | None = None,
    ) -> None:
        self._tile_properties_resolver = (
            tile_properties_resolver
        )
        
    def convert(self, analysis: AnalysisResult) -> ConversionResult:
        grouped_sheets: dict[str, list[SheetInfo]] = defaultdict(list)

        for sheet_info in analysis.sheets:
            grouped_sheets[sheet_info.prefix].append(sheet_info)

        tilesets: list[Tileset] = []

        for name, sheet_infos in sorted(grouped_sheets.items()):
            sheets = tuple(
                self._convert_sheet(
                    name,
                    sheet_info,
                )
                for sheet_info in sorted(
                    sheet_infos,
                    key=self._sheet_order,
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

    def _convert_sheet(
        self,
        tileset_name: str,
        sheet_info: SheetInfo,
    ) -> Sheet:
        tiles = tuple(
            self._resolve_tile_properties(
                self._create_tile(
                    tileset_name=tileset_name,
                    sheet_type=sheet_info.sheet_type,
                    index=index,
                    column=column,
                    row=row,
                    tile_width=sheet_info.tile_width,
                    tile_height=sheet_info.tile_height,
                )
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
        tileset_name: str,
        sheet_type: SheetType,
        index: int,
        column: int,
        row: int,
        tile_width: int,
        tile_height: int,
    ) -> Tile:
        return Tile(
            ref=TileRef(
                tileset=tileset_name,
                sheet_type=sheet_type,
                index=index,
            ),
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
            SheetType.A5: 0,
            SheetType.B: 1,
            SheetType.C: 2,
            SheetType.D: 3,
            SheetType.E: 4,
        }

        return order[sheet_info.sheet_type]

    def _resolve_tile_properties(
        self,
        tile: Tile,
    ) -> Tile:
        """Resolve RPG Maker properties and collision for one tile.

        The resolver is responsible for translating the TileRef into the
        corresponding RPG Maker flags and decoding those flags into
        TileProperties.

        Collision is then derived from the semantic TileProperties.

        Keeping both transformations here ensures that the Tile entering
        the rest of the conversion pipeline is internally consistent:

            TileRef
            │
            ▼
            TilePropertiesResolver
            │
            ▼
            TileProperties
            │
            ▼
            TileCollision
            │
            ▼
            enriched Tile

        When no resolver is configured, the tile is returned unchanged.
        This preserves the converter's previous behaviour.
        """
        
        if self._tile_properties_resolver is None:
            return tile

        properties = (
            self._tile_properties_resolver.resolve(tile)
        )

        collision = tile_properties_to_collision(
            properties,
        )

        return replace(
            tile,
            properties=properties,
            collision=collision,
        )