from pathlib import Path

from rpgmaker2godot.atlas.builder import AtlasBuilder
from rpgmaker2godot.atlas.writer import AtlasWriter
from rpgmaker2godot.model.tileset import ConversionResult


class SimpleExporter:
    """Export a converted RPG Maker tileset to PNG atlases."""

    def __init__(
        self,
        atlas_builder: AtlasBuilder | None = None,
        atlas_writer: AtlasWriter | None = None,
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

            output_path = output_directory / f"{tileset.name}.png"

            self._atlas_writer.write(
                atlas,
                output_path,
            )

            generated_paths.append(output_path)

        return tuple(generated_paths)
