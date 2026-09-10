from pathlib import Path

from rpgmaker2godot.godot.model import (
    GodotAtlasCell,
    GodotAtlasMapping,
    GodotAtlasSource,
    GodotAtlasTile,
    GodotTileAnimation,
    GodotTileSet,
)
from rpgmaker2godot.model import SheetType
from rpgmaker2godot.tileset.autotile.a1 import (
    A1_FRAME_STRIDE,
    A1_SHAPES_PER_AUTOTILE,
    a1_animation_durations,
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

            animation = self._tile_animation(tile.ref)

            if animation is None and self._is_animation_frame(tile.ref):
                # The cell is occupied by an animation frame of the
                # preceding base tile: Godot reserves those cells
                # automatically, they must not be created as tiles.
                continue

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
                    animation=animation,
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

    @staticmethod
    def _is_animation_frame(
        ref,
    ) -> bool:
        """Return whether the TileRef is an A1 animation frame (frame > 0)."""

        return ref.sheet_type == SheetType.A1 and ref.index % A1_FRAME_STRIDE != 0

    @staticmethod
    def _tile_animation(
        ref,
    ) -> GodotTileAnimation | None:
        """Return the animation of an A1 base tile (frame 0), else None.

        Animated waters and waterfalls cycle three frames with the
        engine's per-frame durations; static kinds return None.
        """

        if ref.sheet_type != SheetType.A1:
            return None

        composition, frame = divmod(ref.index, A1_FRAME_STRIDE)

        if frame != 0:
            return None

        durations = a1_animation_durations(composition // A1_SHAPES_PER_AUTOTILE)

        if durations is None:
            return None

        return GodotTileAnimation(
            frames_count=len(durations),
            durations=durations,
        )
