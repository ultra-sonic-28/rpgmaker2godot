from pathlib import Path

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.atlas.writer import AtlasWriter
from rpgmaker2godot.godot.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.resource_writer import GodotResourceWriter
from rpgmaker2godot.godot.tileset_builder import GodotTileSetBuilder
from rpgmaker2godot.model.tileset import ConversionResult


class SimpleExporter:
    """Export converted RPG Maker tilesets as PNG atlases and Godot TileSet resources."""

    def __init__(
        self,
        atlas_builder: AtlasBuilder | None = None,
        atlas_writer: AtlasWriter | None = None,
        godot_atlas_mapper: GodotAtlasMapper | None = None,
        godot_tileset_builder: GodotTileSetBuilder | None = None,
        godot_resource_writer: GodotResourceWriter | None = None,
    ) -> None:
        self._atlas_builder = (
            atlas_builder
            if atlas_builder is not None
            else AtlasBuilder()
        )

        self._atlas_writer = (
            atlas_writer
            if atlas_writer is not None
            else AtlasWriter()
        )

        self._godot_atlas_mapper = (
            godot_atlas_mapper
            if godot_atlas_mapper is not None
            else GodotAtlasMapper()
        )

        self._godot_tileset_builder = (
            godot_tileset_builder
            if godot_tileset_builder is not None
            else GodotTileSetBuilder()
        )

        self._godot_resource_writer = (
            godot_resource_writer
            if godot_resource_writer is not None
            else GodotResourceWriter()
        )

    def export(
        self,
        conversion: ConversionResult,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        generated_paths: list[Path] = []

        for tileset in conversion.tilesets:
            atlas = self._atlas_builder.build(tileset)

            atlas_path = output_directory / f"{tileset.name}.png"

            self._atlas_writer.write(
                atlas,
                atlas_path,
            )

            godot_atlas = self._godot_atlas_mapper.map(atlas)

            godot_tileset = self._godot_tileset_builder.build(
                godot_atlas,
                atlas_path,
            )

            resource_path = (
                output_directory / f"{tileset.name}.tres"
            )

            self._godot_resource_writer.write(
                godot_tileset,
                resource_path,
                atlas_path,
            )

            generated_paths.extend(
                (
                    atlas_path,
                    resource_path,
                )
            )

        return tuple(generated_paths)