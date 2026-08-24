from pathlib import Path

from ..model import (
    GodotAtlasCell,
    GodotAtlasMapping,
    GodotAtlasSource,
    GodotAtlasTile,
    GodotTileSet,
)


class GodotTileSetBuilder:
    """Build a Godot-oriented TileSet representation."""

    def build(
        self,
        mapping: GodotAtlasMapping,
        texture_path: Path,
    ) -> GodotTileSet:

        tiles: list[GodotAtlasTile] = []

        max_column = mapping.width // mapping.tile_width
        max_row = mapping.height // mapping.tile_height

        for tile in mapping.tiles:
            if tile.atlas_x % mapping.tile_width != 0:
                raise ValueError(
                    f"Tile {tile.ref} is not aligned to the atlas grid "
                    f"horizontally: x={tile.atlas_x}"
                )

            if tile.atlas_y % mapping.tile_height != 0:
                raise ValueError(
                    f"Tile {tile.ref} is not aligned to the atlas grid "
                    f"vertically: y={tile.atlas_y}"
                )

            if tile.width <= 0:
                raise ValueError(
                    f"Tile {tile.ref} has invalid width: {tile.width}"
                )

            if tile.height <= 0:
                raise ValueError(
                    f"Tile {tile.ref} has invalid height: {tile.height}"
                )

            if tile.width % mapping.tile_width != 0:
                raise ValueError(
                    f"Tile {tile.ref} has width {tile.width}, "
                    f"which is not aligned to the atlas tile width "
                    f"{mapping.tile_width}"
                )

            if tile.height % mapping.tile_height != 0:
                raise ValueError(
                    f"Tile {tile.ref} has height {tile.height}, "
                    f"which is not aligned to the atlas tile height "
                    f"{mapping.tile_height}"
                )

            column = tile.atlas_x // mapping.tile_width
            row = tile.atlas_y // mapping.tile_height

            cell_width = tile.width // mapping.tile_width
            cell_height = tile.height // mapping.tile_height

            if not 0 <= column < max_column:
                raise ValueError(
                    f"Tile {tile.ref} is outside atlas horizontally: "
                    f"column={column}"
                )

            if not 0 <= row < max_row:
                raise ValueError(
                    f"Tile {tile.ref} is outside atlas vertically: "
                    f"row={row}"
                )

            if column + cell_width > max_column:
                raise ValueError(
                    f"Tile {tile.ref} exceeds atlas width: "
                    f"column={column}, width={cell_width}, "
                    f"max_columns={max_column}"
                )

            if row + cell_height > max_row:
                raise ValueError(
                    f"Tile {tile.ref} exceeds atlas height: "
                    f"row={row}, height={cell_height}, "
                    f"max_rows={max_row}"
                )

            tiles.append(
                GodotAtlasTile(
                    ref=tile.ref,
                    source_x=tile.source_x,
                    source_y=tile.source_y,
                    atlas_x=tile.atlas_x,
                    atlas_y=tile.atlas_y,
                    cell=GodotAtlasCell(
                        column=column,
                        row=row,
                    ),
                    width=tile.width,
                    height=tile.height,
                    collision=tile.collision,
                )
            )

        source = GodotAtlasSource(
            texture_path=texture_path,
            tile_width=mapping.tile_width,
            tile_height=mapping.tile_height,
            texture_width=mapping.width,
            texture_height=mapping.height,
            tiles=tuple(tiles),
        )

        return GodotTileSet(
            tile_width=mapping.tile_width,
            tile_height=mapping.tile_height,
            atlas_sources=(source,),
        )