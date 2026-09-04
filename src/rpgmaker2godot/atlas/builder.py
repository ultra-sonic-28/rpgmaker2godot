from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement, AtlasQuarter
from rpgmaker2godot.model import SheetType, Tileset
from rpgmaker2godot.tileset.autotile.a2 import a2_shape_quarters
from rpgmaker2godot.tileset.autotile.a3 import a3_shape_quarters
from rpgmaker2godot.tileset.autotile.a4 import a4_shape_quarters
from rpgmaker2godot.tileset.autotile.composer import QUARTER_SIZE

# Per autotile sheet type, the engine-backed function returning the
# source quarter pieces of one unfolded (kind, shape) tile. Only used
# as a fallback: converter-produced tiles carry their own quarters
# (needed for the flags-dependent A2 table rendering).
_AUTOTILE_SHAPE_QUARTERS = {
    SheetType.A2: a2_shape_quarters,
    SheetType.A3: a3_shape_quarters,
    SheetType.A4: a4_shape_quarters,
}


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
                if sheet.sheet_type in _AUTOTILE_SHAPE_QUARTERS:
                    placements.append(
                        self._autotile_placement(
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
    def _autotile_placement(
        sheet,
        tile,
        offset_y: int,
    ) -> AtlasPlacement:
        """Build the placement of one unfolded autotile tile (A2-A4).

        The tile's ``ref.index`` encodes ``local_kind * 48 + shape``
        (matching RPG Maker's A2/A3/A4 Tile ID layout). The atlas
        position comes from the tile's packed ``x``/``y`` (set by the
        converter); the source pieces are the tile's stored
        composition — or, for manually built tiles without one, the
        engine shape table (which cannot know the flags-dependent A2
        table rendering). Only distinct tiles reach this stage: the
        converter already dropped the duplicated Wall Side shape IDs
        and every graphically identical variant.
        """

        local_kind = tile.ref.index // 48
        shape = tile.ref.index % 48

        if tile.quarters is not None:
            pieces = tile.quarters
        else:
            shape_quarters = _AUTOTILE_SHAPE_QUARTERS[tile.ref.sheet_type]

            pieces = shape_quarters(local_kind, shape)

        quarters = tuple(
            AtlasQuarter(
                source_x=piece[0],
                source_y=piece[1],
                dest_x=piece[2],
                dest_y=piece[3],
                # Every autotile piece is a 24px-wide crop; the
                # optional fifth element narrows it vertically (the
                # A2 table halves are 12px tall).
                width=QUARTER_SIZE,
                height=piece[4] if len(piece) == 5 else QUARTER_SIZE,
            )
            for piece in pieces
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