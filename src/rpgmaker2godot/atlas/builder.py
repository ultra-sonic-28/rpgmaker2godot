from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement
from rpgmaker2godot.model import Tileset, SheetType


SHEET_ORDER = {
    SheetType.A5: 0,
    SheetType.B: 1,
    SheetType.C: 2,
    SheetType.D: 3,
    SheetType.E: 4,
}


class AtlasBuilder:
    """Build an atlas from all sheets belonging to a tileset."""

    def build(self, tileset: Tileset) -> Atlas:
        sheets = tuple(
            sorted(
                tileset.sheets,
                key=lambda sheet: SHEET_ORDER[sheet.sheet_type],
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