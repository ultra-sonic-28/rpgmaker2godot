from PIL import Image

from rpgmaker2godot.image.source import ImageSource
from rpgmaker2godot.model import Tile


class TileExtractor:
    """Extract tile images from an ImageSource."""

    def extract(
        self,
        source: ImageSource,
        tile: Tile,
    ) -> Image.Image:
        image = source.open()

        box = (
            tile.x,
            tile.y,
            tile.x + tile.width,
            tile.y + tile.height,
        )

        return image.crop(box)