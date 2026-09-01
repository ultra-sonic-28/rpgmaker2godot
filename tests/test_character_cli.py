from pathlib import Path

from PIL import Image

from rpgmaker2godot.cli import main


def create_character_sheet(
    directory: Path,
    filename: str,
    frame_size: tuple[int, int] = (16, 16),
    color: tuple[int, int, int, int] = (255, 0, 0, 255),
) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    width = frame_size[0] * 3
    height = frame_size[1] * 9

    Image.new("RGBA", (width, height), color).save(directory / filename)


def flatten(text: str) -> str:
    """Collapse whitespace runs — panels wrap long lines."""
    return " ".join(text.split())


def test_character_mode_exports_spriteframes(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    create_character_sheet(input_directory, "player-1.png")
    create_character_sheet(input_directory, "player-2.png")

    exit_code = main(
        [
            "--mode",
            "CHARACTER",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0

    # The program banner is displayed on startup.
    assert "rpgmaker2godot v0.1.0" in captured.out

    for name in ("player-1", "player-2"):
        assert (output_directory / f"{name}.png").exists()
        assert (output_directory / f"{name}.tres").exists()

    content = (output_directory / "player-1.tres").read_text(
        encoding="utf-8",
    )

    assert '[gd_resource type="SpriteFrames"' in content
    assert '"name": &"walk-down",' in content
    assert '"name": &"idle-up",' in content
    assert '"name": &"damaged",' in content

    # The pipeline steps are reported in order.
    assert "[1/3] Analyzing input directory" in captured.out
    assert "[2/3] Building sprite frames" in captured.out
    assert "[3/3] Exporting Godot resources" in captured.out

    assert "player-1: 9 animations, 23 frames" in captured.out
    assert "player-1.tres  9 animations (23 frames)" in captured.out

    # The generated files are listed at the end.
    assert "player-1.png" in captured.out
    assert "player-1.tres" in captured.out


def test_character_mode_is_case_insensitive(tmp_path: Path) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    create_character_sheet(input_directory, "player-1.png")

    exit_code = main(
        [
            "--mode",
            "character",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0
    assert (output_directory / "player-1.tres").exists()


def test_character_mode_rejects_simple(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    create_character_sheet(input_directory, "player-1.png")

    exit_code = main(
        [
            "--mode",
            "CHARACTER",
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2

    output = flatten(captured.out.replace("│", " "))

    assert "--simple applies to tileset conversion only." in output
    assert not output_directory.exists()


def test_character_mode_rejects_unknown_mode(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    create_character_sheet(input_directory, "player-1.png")

    exit_code = main(
        [
            "--mode",
            "GHOST",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2

    output = flatten(captured.out.replace("│", " "))

    assert "invalid choice: 'GHOST'" in output
    assert not output_directory.exists()


def test_character_mode_warns_about_tileset_only_options(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    create_character_sheet(input_directory, "player-1.png")

    exit_code = main(
        [
            "--mode",
            "CHARACTER",
            "--no-merge",
            "--tileset",
            "Inside",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0

    stderr = flatten(captured.err.replace("│", " "))

    assert "Tileset-only options --tileset --no-merge ignored" in stderr

    # The conversion is not affected by the ignored options.
    assert (output_directory / "player-1.tres").exists()


def test_character_mode_reports_invalid_sheets(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    create_character_sheet(input_directory, "player-1.png")

    # 50px wide: not divisible by the 3 frame columns.
    Image.new("RGBA", (50, 144)).save(input_directory / "broken.png")

    exit_code = main(
        [
            "--mode",
            "CHARACTER",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0

    assert "Warnings:" in captured.out
    assert "broken.png" in captured.out

    assert (output_directory / "player-1.tres").exists()
    assert not (output_directory / "broken.tres").exists()


def test_character_mode_without_character_sheet_fails(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "characters"
    output_directory = tmp_path / "output"

    input_directory.mkdir(parents=True)

    exit_code = main(
        [
            "--mode",
            "CHARACTER",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    assert "No character spritesheets found" in captured.err
    assert not output_directory.exists()


def test_default_mode_is_tileset(tmp_path: Path, capsys) -> None:
    """Without --mode CHARACTER, the tileset pipeline is used."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    input_directory.mkdir(parents=True)

    Image.new("RGBA", (96, 96), (255, 0, 0, 255)).save(
        input_directory / "Inside_B.png"
    )

    exit_code = main(
        [
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2

    output = flatten(captured.out.replace("│", " "))

    # The tileset pipeline still requires --simple.
    assert "Only --simple mode is currently supported." in output
