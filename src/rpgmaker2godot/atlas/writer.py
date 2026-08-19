from pathlib import Path

from PIL import Image

from rpgmaker2godot.atlas.models import Atlas


class AtlasWriter:
    """Write an internal Atlas to a PNG image."""

    def write(
        self,
        atlas: Atlas,
        output_path: Path,
    ) -> None:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        image = Image.new(
            "RGBA",
            (atlas.width, atlas.height),
            (0, 0, 0, 0),
        )

        source_images: dict[Path, Image.Image] = {}

        try:
            for placement in atlas.placements:
                source = source_images.get(placement.source_path)

                if source is None:
                    source = Image.open(
                        placement.source_path
                    ).convert("RGBA")

                    source_images[
                        placement.source_path
                    ] = source

                region = source.crop(
                    (
                        placement.source_x,
                        placement.source_y,
                        placement.source_x + placement.width,
                        placement.source_y + placement.height,
                    )
                )

                image.alpha_composite(
                    region,
                    (
                        placement.atlas_x,
                        placement.atlas_y,
                    ),
                )

            image.save(output_path, "PNG")

        finally:
            image.close()
            
            for source in source_images.values():
                source.close()