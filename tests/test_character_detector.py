from pathlib import Path

import pytest
from PIL import Image

from rpgmaker2godot.analysis import CharacterDetector


def create_character_sheet(
    directory: Path,
    filename: str,
    frame_size: tuple[int, int] = (16, 16),
) -> None:
    """Create a valid character sheet: 3 frame columns, 9 rows."""

    directory.mkdir(parents=True, exist_ok=True)

    width = frame_size[0] * 3
    height = frame_size[1] * 9

    Image.new("RGBA", (width, height)).save(directory / filename)


def test_detects_character_sheets(tmp_path: Path) -> None:
    create_character_sheet(tmp_path, "player-1.png")
    create_character_sheet(tmp_path, "player-2.png")

    result = CharacterDetector().analyze(tmp_path)

    assert len(result.sheets) == 2
    assert result.warnings == ()

    assert result.sheets[0].path.name == "player-1.png"
    assert result.sheets[1].path.name == "player-2.png"


def test_frame_size_is_derived_from_the_image_size(tmp_path: Path) -> None:
    create_character_sheet(tmp_path, "player-1.png", frame_size=(48, 48))

    result = CharacterDetector().analyze(tmp_path)

    sheet = result.sheets[0]

    assert (sheet.width, sheet.height) == (144, 432)
    assert (sheet.frame_width, sheet.frame_height) == (48, 48)
    assert (sheet.columns, sheet.rows) == (3, 9)


def test_invalid_width_is_reported(tmp_path: Path) -> None:
    create_character_sheet(tmp_path, "player-1.png", frame_size=(16, 16))

    # 49px wide: not divisible by the 3 frame columns.
    Image.new("RGBA", (49, 144)).save(tmp_path / "broken.png")

    result = CharacterDetector().analyze(tmp_path)

    assert len(result.sheets) == 1
    assert len(result.warnings) == 1

    assert "broken.png" in result.warnings[0]
    assert "49px" in result.warnings[0]


def test_invalid_height_is_reported(tmp_path: Path) -> None:
    create_character_sheet(tmp_path, "player-1.png", frame_size=(16, 16))

    # 142px high: not divisible by the 9 animation rows.
    Image.new("RGBA", (48, 142)).save(tmp_path / "broken.png")

    result = CharacterDetector().analyze(tmp_path)

    assert len(result.sheets) == 1
    assert len(result.warnings) == 1

    assert "broken.png" in result.warnings[0]
    assert "142px" in result.warnings[0]


def test_all_invalid_sheets_yield_no_sheet(tmp_path: Path) -> None:
    Image.new("RGBA", (50, 144)).save(tmp_path / "broken.png")

    result = CharacterDetector().analyze(tmp_path)

    assert len(result.sheets) == 0
    assert len(result.warnings) == 1


def test_non_png_files_are_ignored(tmp_path: Path) -> None:
    create_character_sheet(tmp_path, "player-1.png")

    (tmp_path / "Tilesets.json").write_text("[]", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")

    result = CharacterDetector().analyze(tmp_path)

    assert len(result.sheets) == 1


def test_empty_directory_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        CharacterDetector().analyze(tmp_path)


def test_missing_directory_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        CharacterDetector().analyze(tmp_path / "missing")


def test_file_input_fails(tmp_path: Path) -> None:
    create_character_sheet(tmp_path, "player-1.png")

    with pytest.raises(NotADirectoryError):
        CharacterDetector().analyze(tmp_path / "player-1.png")
