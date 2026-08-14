from pathlib import Path

import pytest
from PIL import Image

from rpgmaker2godot.analysis import (
    RPGMakerVersion,
    SheetType,
    TilesetDetector,
)


def create_sheet(
    directory: Path,
    filename: str,
    size: tuple[int, int] = (48 * 8, 48 * 8),
) -> None:
    image = Image.new("RGBA", size)
    image.save(directory / filename)


def test_detects_supported_sheets(tmp_path: Path) -> None:
    create_sheet(tmp_path, "Inside_A5.png")
    create_sheet(tmp_path, "Inside_B.png")
    create_sheet(tmp_path, "Inside_C.png")

    result = TilesetDetector().analyze(tmp_path)

    assert result.version == RPGMakerVersion.UNKNOWN
    assert result.tile_width == 48
    assert result.tile_height == 48

    assert len(result.sheets) == 3

    assert result.sheets[0].sheet_type == SheetType.A5
    assert result.sheets[0].prefix == "Inside"

    assert result.sheets[1].sheet_type == SheetType.B
    assert result.sheets[1].prefix == "Inside"

    assert result.sheets[2].sheet_type == SheetType.C
    assert result.sheets[2].prefix == "Inside"


def test_missing_sheets_are_allowed(tmp_path: Path) -> None:
    create_sheet(tmp_path, "Inside_B.png")

    result = TilesetDetector().analyze(tmp_path)

    assert len(result.sheets) == 1
    assert result.sheets[0].sheet_type == SheetType.B
    assert result.sheets[0].prefix == "Inside"


def test_invalid_dimensions_are_reported(tmp_path: Path) -> None:
    create_sheet(
        tmp_path,
        "Inside_B.png",
        size=(100, 100),
    )

    result = TilesetDetector().analyze(tmp_path)

    assert len(result.sheets) == 0
    assert len(result.warnings) == 1

    assert "Inside_B.png" in result.warnings[0]
    assert "100px" in result.warnings[0]


def test_empty_directory_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        TilesetDetector().analyze(tmp_path)


def test_multiple_tilesets_are_detected(tmp_path: Path) -> None:
    create_sheet(tmp_path, "Inside_A5.png")
    create_sheet(tmp_path, "Inside_B.png")
    create_sheet(tmp_path, "Outside_A5.png")
    create_sheet(tmp_path, "Outside_B.png")

    result = TilesetDetector().analyze(tmp_path)

    assert len(result.sheets) == 4

    prefixes = {
        sheet.prefix
        for sheet in result.sheets
    }

    assert prefixes == {"Inside", "Outside"}


def test_files_without_supported_suffix_are_ignored(
    tmp_path: Path,
) -> None:
    create_sheet(tmp_path, "Inside_A5.png")
    create_sheet(tmp_path, "README.png")
    create_sheet(tmp_path, "Inside_F.png")

    (tmp_path / "Something.jpg").write_bytes(b"not a tileset")

    result = TilesetDetector().analyze(tmp_path)

    assert len(result.sheets) == 1

    assert result.sheets[0].sheet_type == SheetType.A5
    assert result.sheets[0].prefix == "Inside"


def test_sheet_without_prefix_is_supported(tmp_path: Path) -> None:
    create_sheet(tmp_path, "A5.png")
    create_sheet(tmp_path, "B.png")

    result = TilesetDetector().analyze(tmp_path)

    assert len(result.sheets) == 2

    assert result.sheets[0].prefix == ""
    assert result.sheets[1].prefix == ""


def test_lowercase_sheet_names_are_supported(tmp_path: Path) -> None:
    create_sheet(tmp_path, "Inside_a5.png")
    create_sheet(tmp_path, "Inside_b.png")

    result = TilesetDetector().analyze(tmp_path)

    assert len(result.sheets) == 2

    assert result.sheets[0].sheet_type == SheetType.A5
    assert result.sheets[1].sheet_type == SheetType.B

    assert result.sheets[0].prefix == "Inside"
    assert result.sheets[1].prefix == "Inside"