from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement, AtlasQuarter
from rpgmaker2godot.model import SheetType, Tileset
from rpgmaker2godot.tileset.autotile.a4 import a4_shape_quarters


class AtlasBuilder:
    """Build an atlas from all sheets belonging to a tileset."""

    def build(self, tileset: Tileset) -> Atlas:
        sheets = tuple(
            sorted(
                tileset.sheets,
                key=lambda sheet: sheet.sheet_type.order,
            )
        )

        if not sheets:
            return Atlas(
                width=0,
                height=0,
                tile_width=48,
                tile_height=48,
                placements=(),
            )

        tile_width = sheets[0].tile_width
        tile_height = sheets[0].tile_height

        for sheet in sheets:
            if (
                sheet.tile_width != tile_width
                or sheet.tile_height != tile_height
            ):
                raise ValueError(
                    "All sheets in a tileset must use "
                    "the same tile size"
                )

        atlas_width = max(
            sheet.width
            for sheet in sheets
        )

        atlas_height = sum(
            sheet.height
            for sheet in sheets
        )

        placements: list[AtlasPlacement] = []

        offset_y = 0

        for sheet in sheets:
            for tile in sheet.tiles:
                if sheet.sheet_type == SheetType.A4:
                    placements.append(
                        self._a4_placement(
                            sheet,
                            tile,
                            offset_y,
                        )
                    )
                else:
                    placements.append(
                        AtlasPlacement(
                            tile=tile.ref,
                            source_path=sheet.source_path,
                            source_x=tile.x,
                            source_y=tile.y,
                            atlas_x=tile.x,
                            atlas_y=offset_y + tile.y,
                            width=tile.width,
                            height=tile.height,
                            collision=tile.collision,
                        )
                    )

            offset_y += sheet.height

        return Atlas(
            width=atlas_width,
            height=atlas_height,
            tile_width=tile_width,
            tile_height=tile_height,
            placements=tuple(placements),
        )

    @staticmethod
    def _a4_placement(
        sheet,
        tile,
        offset_y: int,
    ) -> AtlasPlacement:
        """Build the placement of one unfolded A4 autotile tile.

        The tile's ``ref.index`` encodes ``local_kind * 48 + shape``
        (matching RPG Maker's A4 Tile ID layout), so the four source
        quarters can be recovered without extra state. The atlas
        position comes from the tile's packed ``x``/``y`` (set by the
        converter); the source piece is whatever the engine's shape
        table dictates. Only distinct tiles reach this stage: the
        converter already dropped the duplicated Wall Side shape IDs
        and every graphically identical variant.
        """

        local_kind = tile.ref.index // 48
        shape = tile.ref.index % 48

        quarters = tuple(
            AtlasQuarter(
                source_x=qx,
                source_y=qy,
                dest_x=dx,
                dest_y=dy,
                # Every A4 quarter is a square 24px crop.
                width=24,
                height=24,
            )
            for qx, qy, dx, dy in a4_shape_quarters(
                local_kind,
                shape,
            )
        )

        return AtlasPlacement(
            tile=tile.ref,
            source_path=sheet.source_path,
            source_x=tile.x,
            source_y=tile.y,
            atlas_x=tile.x,
            atlas_y=offset_y + tile.y,
            width=tile.width,
            height=tile.height,
            collision=tile.collision,
            quarters=quarters,
        )