import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from rpgmaker2godot.model import SheetType

from .models import (
    AnalysisResult,
    RPGMakerVersion,
    SheetInfo,
)

SHEET_PATTERN = re.compile(
    r"^(?P<prefix>.*_)?(?P<sheet>A2|A3|A4|A5|B|C|D|E)\.png$",
    re.IGNORECASE,
)

DEFAULT_TILE_SIZE = 48


class TilesetDetector:
    def __init__(self, tile_size: int = DEFAULT_TILE_SIZE) -> None:
        self.tile_size = tile_size

    def analyze(self, directory: Path) -> AnalysisResult:
        if not directory.exists():
            raise FileNotFoundError(
                f"Input directory does not exist: {directory}"
            )

        if not directory.is_dir():
            raise NotADirectoryError(
                f"Input path is not a directory: {directory}"
            )

        sheets: list[SheetInfo] = []
        warnings: list[str] = []
        found_sheets = False

        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue

            match = SHEET_PATTERN.match(path.name)

            if match is None:
                continue

            sheet_name = match.group("sheet").upper()
            sheet_type = SheetType(sheet_name)

            found_sheets = True

            try:
                prefix = match.group("prefix") or ""

                prefix = prefix.removesuffix("_")

                sheet = self._analyze_sheet(
                    path,
                    sheet_type,
                    prefix,
                )
            except ValueError as error:
                warnings.append(str(error))
                continue

            sheets.append(sheet)

        if not found_sheets:
            raise ValueError(
                "No supported RPG Maker MV/MZ sheets found "
                "(expected files ending with A2.png, A3.png, A4.png, "
                "A5.png, B.png, C.png, D.png or E.png)."
            )

        return AnalysisResult(
            input_directory=directory,
            version=RPGMakerVersion.UNKNOWN,
            tile_width=self.tile_size,
            tile_height=self.tile_size,
            sheets=tuple(sheets),
            warnings=tuple(warnings),
        )

    def _analyze_sheet(
        self,
        path: Path,
        sheet_type: SheetType,
        prefix: str = "",
    ) -> SheetInfo:
        try:
            with Image.open(path) as image:
                width, height = image.size

        except UnidentifiedImageError as error:
            raise ValueError(
                f"{path.name}: invalid or unsupported PNG image."
            ) from error

        if width % self.tile_size != 0:
            raise ValueError(
                f"{path.name}: width {width}px is not divisible "
                f"by tile size {self.tile_size}px."
            )

        if height % self.tile_size != 0:
            raise ValueError(
                f"{path.name}: height {height}px is not divisible "
                f"by tile size {self.tile_size}px."
            )

        return SheetInfo(
            sheet_type=sheet_type,
            path=path,
            prefix=prefix,
            width=width,
            height=height,
            tile_width=self.tile_size,
            tile_height=self.tile_size,
            columns=width // self.tile_size,
            rows=height // self.tile_size,
        )