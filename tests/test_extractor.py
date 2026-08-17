from pathlib import Path

from PIL import Image

from rpgmaker2godot.image import ImageSource, TileExtractor
from rpgmaker2godot.model import Tile


def test_extracts_tile(tmp_path: Path) -> None:
    path = tmp_path / "test.png"

    image = Image.new("RGBA", (144, 144))
    image.save(path)
    image.close()

    source = ImageSource(path)

    tile = Tile(
        index=17,
        column=1,
        row=2,
        x=48,
        y=96,
        width=48,
        height=48,
    )

    extracted = TileExtractor().extract(
        source,
        tile,
    )

    assert extracted.size == (48, 48)

    source.close()


def test_extracts_correct_region(tmp_path: Path) -> None:
    path = tmp_path / "test.png"

    image = Image.new("RGBA", (96, 96))

    image.paste((255, 0, 0, 255), (0, 0, 48, 48))
    image.paste((0, 255, 0, 255), (48, 0, 96, 48))
    image.paste((0, 0, 255, 255), (0, 48, 48, 96))
    image.paste((255, 255, 0, 255), (48, 48, 96, 96))

    image.save(path)
    image.close()

    source = ImageSource(path)

    tile = Tile(
        index=3,
        column=1,
        row=1,
        x=48,
        y=48,
        width=48,
        height=48,
    )

    extracted = TileExtractor().extract(
        source,
        tile,
    )

    assert extracted.size == (48, 48)
    assert extracted.getpixel((0, 0)) == (
        255,
        255,
        0,
        255,
    )

    source.close()