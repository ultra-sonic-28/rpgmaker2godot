from pathlib import Path

from rpgmaker2godot.godot.atlas.atlas_builder import GodotAtlasSourceBuilder
from rpgmaker2godot.godot.resource.path import to_godot_path

from ..model import GodotTileSet
from .resource import (
    GodotExtResource,
    GodotTileSetResource,
)
from .resource_serializer import GodotResourceSerializer


class GodotResourceWriter:
    """Write a Godot TileSet resource to a .tres file."""

    def __init__(
        self,
        serializer: GodotResourceSerializer | None = None,
        atlas_source_builder: GodotAtlasSourceBuilder | None = None,
    ) -> None:
        self._serializer = (
            serializer
            if serializer is not None
            else GodotResourceSerializer()
        )

        self._atlas_source_builder = (
            atlas_source_builder
            if atlas_source_builder is not None
            else GodotAtlasSourceBuilder()
        )

    def write(
        self,
        tileset: GodotTileSet,
        output_path: Path,
        texture_path: Path,
        terrain_plan=None,
    ) -> None:
        resource = self._build_resource(
            tileset,
            output_path,
            texture_path,
            terrain_plan,
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
        terrain_plan=None,
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

        atlas = self._atlas_source_builder.build(
            source,
            resource_id=atlas_resource_id,
            texture_resource_id=texture_resource_id,
            terrain_plan=terrain_plan,
        )

        has_physics_layer = any(
            tile.collision is not None
            for tile in atlas.tiles
        )

        return GodotTileSetResource(
            tile_width=tileset.tile_width,
            tile_height=tileset.tile_height,
            texture=texture,
            atlas_source=atlas,
            has_physics_layer=has_physics_layer,
            terrain_sets=(
                terrain_plan.terrain_sets if terrain_plan else ()
            ),
        )

    @staticmethod
    def _to_godot_path(
        resource_path: Path,
        texture_path: Path,
    ) -> str:
        return to_godot_path(
            resource_path,
            texture_path,
        )