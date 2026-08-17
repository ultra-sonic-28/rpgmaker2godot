from rpgmaker2godot.atlas.models import Atlas, AtlasPlacement
from rpgmaker2godot.model import Sheet


class AtlasBuilder:
    """Build an atlas layout from a regular RPG Maker sheet."""

    def build(self, sheet: Sheet) -> Atlas:
        width = sheet.columns * sheet.tile_width
        height = sheet.rows * sheet.tile_height

        placements = tuple(
            AtlasPlacement(
                tile=tile.ref,
                x=tile.column * sheet.tile_width,
                y=tile.row * sheet.tile_height,
            )
            for tile in sheet.tiles
        )

        return Atlas(
            width=width,
            height=height,
            tile_width=sheet.tile_width,
            tile_height=sheet.tile_height,
            placements=placements,
        )