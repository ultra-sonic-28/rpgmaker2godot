from pathlib import Path

from PIL import Image

from rpgmaker2godot.cli import main


def create_sheet(
    directory: Path,
    filename: str,
    size: tuple[int, int] = (96, 96),
    color: tuple[int, int, int, int] = (255, 0, 0, 255),
) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    Image.new(
        "RGBA",
        size,
        color,
    ).save(directory / filename)


def test_simple_cli_exports_tileset(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_A5.png",
        color=(255, 0, 0, 255),
    )

    create_sheet(
        input_directory,
        "Inside_B.png",
        color=(0, 255, 0, 255),
    )

    create_sheet(
        input_directory,
        "Inside_C.png",
        color=(0, 0, 255, 255),
    )

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    output_path = output_directory / "Inside.png"

    assert output_path.exists()

    with Image.open(output_path) as image:
        assert image.size == (96, 288)

    captured = capsys.readouterr()

    assert "Inside.png" in captured.out


def test_simple_cli_exports_multiple_tilesets(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    for tileset, colors in (
        (
            "Inside",
            (
                (255, 0, 0, 255),
                (0, 255, 0, 255),
                (0, 0, 255, 255),
            ),
        ),
        (
            "Outside",
            (
                (255, 255, 0, 255),
                (255, 0, 255, 255),
                (0, 255, 255, 255),
            ),
        ),
    ):
        for sheet_type, color in zip(
            ("A5", "B", "C"),
            colors,
        ):
            create_sheet(
                input_directory,
                f"{tileset}_{sheet_type}.png",
                color=color,
            )

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    inside = output_directory / "Inside.png"
    outside = output_directory / "Outside.png"

    assert inside.exists()
    assert outside.exists()

    with Image.open(inside) as image:
        assert image.size == (96, 288)

    with Image.open(outside) as image:
        assert image.size == (96, 288)


def test_simple_cli_reports_missing_input_directory(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "does-not-exist"
    output_directory = tmp_path / "output"

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code != 0

    captured = capsys.readouterr()

    assert "does not exist" in captured.err


def test_simple_cli_reports_empty_input_directory(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code != 0

    captured = capsys.readouterr()

    assert "No supported RPG Maker MV/MZ sheets found" in captured.err