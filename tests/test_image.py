from pathlib import Path

from PIL import Image

from rpgmaker2godot.image import ImageSource


def test_image_source_is_lazy(tmp_path: Path) -> None:
    path = tmp_path / "test.png"

    image = Image.new("RGBA", (96, 96))
    image.save(path)
    image.close()

    source = ImageSource(path)

    assert source._image is None

    opened = source.open()

    assert source._image is opened
    assert opened.size == (96, 96)

    source.close()

    assert source._image is None


def test_image_source_reuses_open_image(tmp_path: Path) -> None:
    path = tmp_path / "test.png"

    image = Image.new("RGBA", (96, 96))
    image.save(path)
    image.close()

    source = ImageSource(path)

    first = source.open()
    second = source.open()

    assert first is second

    source.close()