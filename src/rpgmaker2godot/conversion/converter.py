from collections import defaultdict
from collections.abc import Iterator
from dataclasses import replace

from rpgmaker2godot.analysis.models import AnalysisResult, SheetInfo
from rpgmaker2godot.model import (
    ConversionResult,
    Sheet,
    Tile,
    TileRef,
    Tileset,
)
from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.tileset.autotile.a4 import (
    A4_AUTOTILE_COUNT,
    A4_HEIGHT,
    A4_PACK_COLUMNS,
    A4_PACK_HEIGHT,
    A4_PACK_ROWS,
    A4_PACK_WIDTH,
    A4_SHAPES_PER_AUTOTILE,
    A4_WIDTH,
)
from rpgmaker2godot.tileset.collision import tile_properties_to_collision
from rpgmaker2godot.tileset.resolver import TilePropertiesResolver
from rpgmaker2godot.tileset.tile_id import tile_to_tile_id


class SimpleConverter:
    """Convert an AnalysisResult into the internal representation."""

    def __init__(
        self,
        *,
        tile_properties_resolver: TilePropertiesResolver | None = None,
        no_merge: bool = False,
    ) -> None:
        self._tile_properties_resolver = (
            tile_properties_resolver
        )

        # When enabled, keep the source sheet split: one converted
        # Tileset per input sheet instead of grouping them by prefix.
        self._no_merge = no_merge

    def convert(self, analysis: AnalysisResult) -> ConversionResult:
        tilesets: list[Tileset] = []

        if self._no_merge:
            for sheet_info in analysis.sheets:
                # Output tileset named after the source sheet (one PNG +
                # .tres per input sheet). The TileRef keeps the RPG name
                # (the prefix) so collision lookup against Tilesets.json
                # still resolves to the same tileset as in merge mode.
                tilesets.append(
                    Tileset(
                        name=sheet_info.path.stem,
                        sheets=(
                            self._convert_sheet(
                                sheet_info.prefix,
                                sheet_info,
                            ),
                        ),
                    )
                )
        else:
            grouped_sheets: dict[str, list[SheetInfo]] = defaultdict(list)

            for sheet_info in analysis.sheets:
                grouped_sheets[sheet_info.prefix].append(sheet_info)

            for name, sheet_infos in sorted(grouped_sheets.items()):
                sheets = tuple(
                    self._convert_sheet(
                        name,
                        sheet_info,
                    )
                    for sheet_info in sorted(
                        sheet_infos,
                        key=lambda info: info.sheet_type.order,
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
        if sheet_info.sheet_type == SheetType.A4:
            return self._convert_a4_sheet(
                tileset_name,
                sheet_info,
            )

        tiles = tuple(
            self._resolve_tile_properties(tile)
            for tile in self._sheet_tiles(
                tileset_name,
                sheet_info,
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

    def _convert_a4_sheet(
        self,
        tileset_name: str,
        sheet_info: SheetInfo,
    ) -> Sheet:
        """Convert an A4 wall-autotile sheet into its unfolded tiles.

        The A4 sheet (``*_A4.png``, 768x720) stores 48 autotile
        **sources**: 8 columns of 96px x 6 vertical slots, alternating
        Wall Top (96x144) and Wall Side (96x96). Following the
        authoritative mapping in ``rmmz_core.js``, each of the 48
        autotiles is unfolded into its 48 connection variants (48x48),
        producing 2304 ready-to-place tiles.

        The sheet's conversion metadata describes the **packed**
        result (16 tiles per row, matching the other sheets' 768px
        width), not the source image.
        """

        if (
            sheet_info.width != A4_WIDTH
            or sheet_info.height != A4_HEIGHT
        ):
            raise ValueError(
                f"{sheet_info.path.name}: A4 sheets must be "
                f"{A4_WIDTH}x{A4_HEIGHT}px, got "
                f"{sheet_info.width}x{sheet_info.height}px."
            )

        tiles: list[Tile] = []

        for local_kind in range(A4_AUTOTILE_COUNT):
            for shape in range(A4_SHAPES_PER_AUTOTILE):
                index = local_kind * A4_SHAPES_PER_AUTOTILE + shape
                column = local_kind % 8
                row = local_kind // 8

                x = (index % A4_PACK_COLUMNS) * 48
                y = (index // A4_PACK_COLUMNS) * 48

                tile = self._create_tile(
                    tileset_name=tileset_name,
                    sheet_type=SheetType.A4,
                    index=index,
                    column=column,
                    row=row,
                    x=x,
                    y=y,
                    width=48,
                    height=48,
                )

                tiles.append(
                    self._resolve_tile_properties(tile)
                )

        return Sheet(
            sheet_type=SheetType.A4,
            source_path=sheet_info.path,
            width=A4_PACK_WIDTH,
            height=A4_PACK_HEIGHT,
            tile_width=48,
            tile_height=48,
            columns=A4_PACK_COLUMNS,
            rows=A4_PACK_ROWS,
            tiles=tuple(tiles),
        )

    def _sheet_tiles(
        self,
        tileset_name: str,
        sheet_info: SheetInfo,
    ) -> Iterator[Tile]:
        """Stream the tiles of a regular (non-A4) sheet grid."""
        geometry = (
            (
                column * sheet_info.tile_width,
                row * sheet_info.tile_height,
                sheet_info.tile_width,
                sheet_info.tile_height,
                column,
                row,
            )
            for row, column in self._tile_coordinates(
                columns=sheet_info.columns,
                rows=sheet_info.rows,
            )
        )

        for index, (x, y, width, height, column, row) in enumerate(geometry):
            yield self._create_tile(
                tileset_name=tileset_name,
                sheet_type=sheet_info.sheet_type,
                index=index,
                column=column,
                row=row,
                x=x,
                y=y,
                width=width,
                height=height,
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
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> Tile:
        return Tile(
            ref=TileRef(
                tileset=tileset_name,
                sheet_type=sheet_type,
                index=index,
            ),
            column=column,
            row=row,
            x=x,
            y=y,
            width=width,
            height=height,
        )

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
            tile_id=tile_to_tile_id(tile),
            coord=(tile.column, tile.row),
        )

        return replace(
            tile,
            properties=properties,
            collision=collision,
        )