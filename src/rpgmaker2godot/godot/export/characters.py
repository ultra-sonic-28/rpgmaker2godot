from pathlib import Path

from PIL import Image

from rpgmaker2godot.character.models import CharacterConversionResult
from rpgmaker2godot.godot.spriteframes.writer import GodotSpriteFramesWriter


class CharacterExporter:
    """Export converted character spritesheets as Godot resources.

    A character spritesheet is exported as-is — the animations are
    natively laid out inside the image — so the exporter copies the
    source PNG into the output directory and writes one
    ``SpriteFrames`` ``.tres`` resource referencing it.
    """

    def __init__(
        self,
        godot_spriteframes_writer: GodotSpriteFramesWriter | None = None,
        godot_project_root: Path | None = None,
        godot_output_path: str | None = None,
    ) -> None:
        self._godot_spriteframes_writer = (
            godot_spriteframes_writer
            if godot_spriteframes_writer is not None
            else GodotSpriteFramesWriter()
        )

        self._godot_project_root = godot_project_root

        # Directory, relative to res://, where the generated
        # spritesheets will be stored in the Godot project
        # (character.path from rpgmaker2godot.yaml). When set, the
        # .tres references "<name>.png" through this path.
        self._godot_output_path = godot_output_path

    def export(
        self,
        conversion: CharacterConversionResult,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        generated_paths: list[Path] = []

        for sheet in conversion.sheets:
            texture_path = (
                output_directory / f"{sheet.name}.png"
            )

            self._copy_texture(
                sheet.source_path,
                texture_path,
            )

            resource_path = (
                output_directory / f"{sheet.name}.tres"
            )

            if self._godot_output_path is not None:
                godot_texture_path = Path(
                    f"res://{self._godot_output_path}/{sheet.name}.png",
                )
            elif self._godot_project_root is None:
                godot_texture_path = Path(
                    texture_path.name,
                )
            else:
                godot_texture_path = texture_path.relative_to(
                    self._godot_project_root,
                )

            self._godot_spriteframes_writer.write(
                sheet,
                resource_path,
                godot_texture_path,
            )

            generated_paths.extend(
                (
                    texture_path,
                    resource_path,
                )
            )

        return tuple(generated_paths)

    @staticmethod
    def _copy_texture(
        source_path: Path,
        output_path: Path,
    ) -> None:
        with Image.open(source_path) as image:
            rgba = image.convert("RGBA")

            try:
                rgba.save(output_path, "PNG")
            finally:
                rgba.close()
