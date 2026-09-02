from collections.abc import Mapping
from pathlib import Path

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.atlas.writer import AtlasWriter
from rpgmaker2godot.godot.atlas.atlas_mapper import GodotAtlasMapper
from rpgmaker2godot.godot.resource.resource_writer import GodotResourceWriter
from rpgmaker2godot.godot.terrain.terrain_builder import (
    GodotTerrainBuilder,
    TerrainResolution,
)
from rpgmaker2godot.godot.tileset.tileset_builder import GodotTileSetBuilder
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
        godot_project_root: Path | None = None,
        godot_output_path: str | None = None,
        terrains: bool = True,
        godot_terrain_builder: GodotTerrainBuilder | None = None,
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

        self._godot_project_root = godot_project_root

        # Directory, relative to res://, where the generated textures
        # will be stored in the Godot project (tileset.path /
        # character.path from rpgmaker2godot.yaml). When set, the
        # .tres references "<output name>.png" through this path.
        self._godot_output_path = godot_output_path

        self._terrains = terrains

        self._godot_terrain_builder = (
            godot_terrain_builder
            if godot_terrain_builder is not None
            else GodotTerrainBuilder()
        )

    def export(
        self,
        conversion: ConversionResult,
        output_directory: Path,
        terrain_resolutions: Mapping[str, TerrainResolution] | None = None,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        generated_paths: list[Path] = []

        for tileset in conversion.tilesets:
            atlas = self._atlas_builder.build(tileset)

            atlas_path = (
                output_directory / f"{tileset.name}.png"
            )

            self._atlas_writer.write(
                atlas,
                atlas_path,
            )

            godot_atlas = self._godot_atlas_mapper.map(atlas)

            godot_tileset = self._godot_tileset_builder.build(
                godot_atlas,
                atlas_path,
            )

            terrain_plan = None

            if self._terrains:
                # Reuse a plan resolved earlier by the CLI when available
                # (the "Resolving terrain definitions" phase) so the A4
                # source image is scanned only once; otherwise resolve it
                # on the fly, preserving the standalone behaviour.
                resolution = (
                    terrain_resolutions[tileset.name]
                    if terrain_resolutions is not None
                    else self._godot_terrain_builder.resolve(tileset)
                )

                terrain_plan = self._godot_terrain_builder.assign(
                    godot_tileset,
                    resolution,
                )

            resource_path = (
                output_directory / f"{tileset.name}.tres"
            )

            if self._godot_output_path is not None:
                godot_texture_path = Path(
                    f"res://{self._godot_output_path}/{tileset.name}.png",
                )
            elif self._godot_project_root is None:
                godot_texture_path = Path(
                    atlas_path.name,
                )
            else:
                godot_texture_path = atlas_path.relative_to(
                    self._godot_project_root,
                )

            self._godot_resource_writer.write(
                godot_tileset,
                resource_path,
                godot_texture_path,
                terrain_plan=terrain_plan,
            )

            generated_paths.extend(
                (
                    atlas_path,
                    resource_path,
                    godot_texture_path,
                )
            )

        return tuple(generated_paths)