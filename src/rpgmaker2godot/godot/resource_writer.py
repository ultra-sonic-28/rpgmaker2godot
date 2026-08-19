from pathlib import Path

from .resource import (
    GodotAtlasSourceResource,
    GodotExtResource,
    GodotTileSetResource,
)
from .resource_serializer import GodotResourceSerializer
from .model import GodotTileSet


class GodotResourceWriter:
    """Write a Godot TileSet resource to a .tres file."""

    def __init__(
        self,
        serializer: GodotResourceSerializer | None = None,
    ) -> None:
        self._serializer = (
            serializer
            if serializer is not None
            else GodotResourceSerializer()
        )

    def write(
        self,
        tileset: GodotTileSet,
        output_path: Path,
        texture_path: Path,
    ) -> None:
        resource = self._build_resource(
            tileset,
            output_path,
            texture_path,
        )

        content = self._serializer.serialize(resource)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            content,
            encoding="utf-8",
        )

    def _build_resource(
        self,
        tileset: GodotTileSet,
        output_path: Path,
        texture_path: Path,
    ) -> GodotTileSetResource:
        if len(tileset.atlas_sources) != 1:
            raise ValueError(
                "The simple Godot resource writer currently supports "
                "exactly one atlas source."
            )

        source = tileset.atlas_sources[0]

        texture_resource_id = "1_texture"
        atlas_resource_id = "TileSetAtlasSource_1"

        texture = GodotExtResource(
            resource_id=texture_resource_id,
            resource_type="Texture2D",
            path=self._to_godot_path(
                output_path,
                texture_path,
            ),
        )

        tiles = tuple(
            (
                tile.cell.column,
                tile.cell.row,
            )
            for tile in source.tiles
        )

        atlas = GodotAtlasSourceResource(
            resource_id=atlas_resource_id,
            texture_resource_id=texture_resource_id,
            tile_width=source.tile_width,
            tile_height=source.tile_height,
            tiles=tiles,
        )

        return GodotTileSetResource(
            tile_width=tileset.tile_width,
            tile_height=tileset.tile_height,
            texture=texture,
            atlas_source=atlas,
        )

    @staticmethod
    def _to_godot_path(
        resource_path: Path,
        texture_path: Path,
    ) -> str:
        normalized = texture_path.as_posix()

        # Déjà un chemin Godot.
        if normalized.startswith("res://"):
            return normalized

        # Chemin relatif : il est déjà relatif à la racine Godot.
        if not texture_path.is_absolute():
            return f"res://{normalized.lstrip('/')}"

        # Chemin absolu : il doit être dans le même arbre que le .tres.
        try:
            relative_path = texture_path.relative_to(
                resource_path.parent,
            )
        except ValueError:
            raise ValueError(
                "Texture path must be located inside the "
                "Godot resource directory: "
                f"{texture_path}"
            ) from None

        return f"res://{relative_path.as_posix()}"