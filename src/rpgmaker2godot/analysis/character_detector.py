from pathlib import Path

from PIL import Image, UnidentifiedImageError

from rpgmaker2godot.character.layout import COLUMNS, ROWS

from .models import CharacterAnalysisResult, CharacterSheetInfo


class CharacterDetector:
    """Detect character spritesheets in an input directory.

    Character sheets cannot be told apart from other PNG files by
    their name alone (any ``player-1.png``-style file may be a
    character), so the CLI ``--character`` switch selects this
    detector explicitly instead of relying on a risky heuristic.

    Every ``.png`` file of the directory is validated against the
    fixed character layout: three frames per row at most and nine
    animation rows, so the frame size is derived from the image size.
    """

    def __init__(
        self,
        columns: int = COLUMNS,
        rows: int = ROWS,
    ) -> None:
        self.columns = columns
        self.rows = rows

    def analyze(
        self,
        directory: Path,
    ) -> CharacterAnalysisResult:
        if not directory.exists():
            raise FileNotFoundError(
                f"Input directory does not exist: {directory}"
            )

        if not directory.is_dir():
            raise NotADirectoryError(
                f"Input path is not a directory: {directory}"
            )

        sheets: list[CharacterSheetInfo] = []
        warnings: list[str] = []
        found_png = False

        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue

            if path.suffix.lower() != ".png":
                continue

            found_png = True

            try:
                sheet = self._analyze_sheet(path)
            except ValueError as error:
                warnings.append(str(error))
                continue

            sheets.append(sheet)

        if not found_png:
            raise ValueError(
                "No character spritesheets found (expected PNG files "
                "such as player-1.png storing the walk, idle and "
                "damaged animations)."
            )

        return CharacterAnalysisResult(
            input_directory=directory,
            sheets=tuple(sheets),
            warnings=tuple(warnings),
        )

    def _analyze_sheet(
        self,
        path: Path,
    ) -> CharacterSheetInfo:
        try:
            with Image.open(path) as image:
                width, height = image.size

        except UnidentifiedImageError as error:
            raise ValueError(
                f"{path.name}: invalid or unsupported PNG image."
            ) from error

        if width % self.columns != 0:
            raise ValueError(
                f"{path.name}: width {width}px is not divisible by "
                f"{self.columns} (the three animation frames "
                f"per row)."
            )

        if height % self.rows != 0:
            raise ValueError(
                f"{path.name}: height {height}px is not divisible by "
                f"{self.rows} (the nine animation rows)."
            )

        return CharacterSheetInfo(
            path=path,
            width=width,
            height=height,
            frame_width=width // self.columns,
            frame_height=height // self.rows,
            columns=self.columns,
            rows=self.rows,
        )
