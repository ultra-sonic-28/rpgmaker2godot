import math
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import replace

from PIL import Image

from rpgmaker2godot.analysis.models import AnalysisResult, SheetInfo
from rpgmaker2godot.model import (
    ConversionResult,
    Sheet,
    Tile,
    TileRef,
    Tileset,
)
from rpgmaker2godot.model.enums import SheetType
from rpgmaker2godot.model.tile_collision import TileCollision
from rpgmaker2godot.tileset.autotile.a4 import (
    A4_HEIGHT,
    A4_PACK_COLUMNS,
    A4_PACK_WIDTH,
    A4_SHAPES_PER_AUTOTILE,
    A4_WIDTH,
    a4_unique_tiles,
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
        autotiles is unfolded into its 48 connection variants (48x48).

        RPG Maker reserves 48 shape IDs per kind although the Wall Side
        table only holds 16 shapes: those extra IDs compose
        pixel-identical tiles. Only the **graphically distinct** tiles
        are kept (``a4_unique_tiles``): the 2304 raw variants reduce to
        1536 distinct compositions, then to the image-dependent number
        of tiles that truly render differently — 1390 for the stock
        ``Inside_A4.png``. Graphically identical tiles stay separate
        when they resolve to a different collision.

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

        source = Image.open(sheet_info.path).convert("RGBA")

        try:
            unique = list(
                a4_unique_tiles(
                    source,
                    dedup_key=self._a4_dedup_key(tileset_name),
                )
            )
        finally:
            source.close()

        tiles: list[Tile] = []

        for index, _quarters in unique:
            local_kind = index // A4_SHAPES_PER_AUTOTILE

            # Packed atlas position: insertion order on the 16-per-row
            # grid (duplicated variants were already skipped).
            slot = len(tiles)
            x = (slot % A4_PACK_COLUMNS) * 48
            y = (slot // A4_PACK_COLUMNS) * 48

            tile = self._create_tile(
                tileset_name=tileset_name,
                sheet_type=SheetType.A4,
                index=index,
                column=local_kind % 8,
                row=local_kind // 8,
                x=x,
                y=y,
                width=48,
                height=48,
            )

            tiles.append(
                self._resolve_tile_properties(tile)
            )

        pack_rows = math.ceil(len(tiles) / A4_PACK_COLUMNS)

        return Sheet(
            sheet_type=SheetType.A4,
            source_path=sheet_info.path,
            width=A4_PACK_WIDTH,
            height=pack_rows * 48,
            tile_width=48,
            tile_height=48,
            columns=A4_PACK_COLUMNS,
            rows=pack_rows,
            tiles=tuple(tiles),
        )

    def _a4_dedup_key(
        self,
        tileset_name: str,
    ) -> Callable[[int, bytes], tuple[bytes, TileCollision]] | None:
        """Build the duplicate-identity hook for the A4 pixel dedup.

        Without a properties resolver, tiles are identified by their
        pixel content alone. With one, two graphically identical tiles
        are only merged when they also resolve to the same directional
        collision: RPG Maker flags live on the engine Tile IDs, so two
        autotile kinds can look exactly the same while allowing a
        different passage.
        """

        if self._tile_properties_resolver is None:
            return None

        def dedup_key(
            index: int,
            signature: bytes,
        ) -> tuple[bytes, TileCollision]:
            tile = Tile(
                ref=TileRef(
                    tileset=tileset_name,
                    sheet_type=SheetType.A4,
                    index=index,
                ),
                column=0,
                row=0,
                x=0,
                y=0,
                width=48,
                height=48,
            )

            properties = (
                self._tile_properties_resolver.resolve(tile)
            )

            collision = tile_properties_to_collision(
                properties,
                tile_id=tile_to_tile_id(tile),
            )

            return signature, collision

        return dedup_key

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