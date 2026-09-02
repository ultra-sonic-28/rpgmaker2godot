from pathlib import Path
from typing import Self

from PIL import Image


class ImageSource:
    """Lazy access to an image file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._image: Image.Image | None = None

    def open(self) -> Image.Image:
        """Open the source image lazily."""
        if self._image is None:
            self._image = Image.open(self.path)

        return self._image

    def close(self) -> None:
        """Close the opened image, if any."""
        if self._image is not None:
            self._image.close()
            self._image = None

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()