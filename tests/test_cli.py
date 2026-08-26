import json
import logging
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


def create_tilesets_json(directory: Path) -> None:
    blocked = 0x000F
    open_tile = 0x0000

    # Global Tile IDs used by a 96x96 Inside_B sheet (2x2 tiles):
    #   (column=0, row=0) -> 0,   (1, 0) -> 1,
    #   (column=0, row=1) -> 16,  (1, 1) -> 17.
    flags = (
        [blocked, blocked]
        + [open_tile] * 14
        + [open_tile, blocked]
    )

    data = [
        None,
        {
            "id": 1,
            "name": "Inside",
            "flags": flags,
        },
    ]

    (directory / "Tilesets.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )


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

    # The program banner is displayed on startup.
    assert "rpgmaker2godot v0.1.0" in captured.out

    # Pipeline steps are reported in order.
    assert "[1/4] Analyzing input directory" in captured.out
    assert "[2/4] Resolving collision flags" in captured.out
    assert "[3/4] Converting tiles" in captured.out
    assert "[4/4] Exporting Godot resources" in captured.out

    # The conversion step reports tiles per tileset.
    assert "Inside: 12 tiles from 3 sheets" in captured.out

    # The export step reports the resulting tile grid.
    assert "(2x6 tiles)" in captured.out
    assert "Inside.tres  2x6 tiles" in captured.out


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


def test_simple_cli_paints_output_when_colors_forced(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_A5.png",
        color=(255, 0, 0, 255),
    )

    monkeypatch.setenv("FORCE_COLOR", "1")

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()

    # Singular forms are used for a single tileset sheet.
    assert "Inside: 4 tiles from 1 sheet" in captured.out

    # White on blue step headings.
    assert "\x1b[97;44m[1/4] Analyzing input directory" in captured.out
    # White on green Generated heading.
    assert "\x1b[97;42mGenerated:" in captured.out


def test_simple_cli_never_paints_when_no_color_is_set(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_A5.png",
        color=(255, 0, 0, 255),
    )

    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()

    # NO_COLOR takes precedence over FORCE_COLOR.
    assert "[1/4] Analyzing input directory" in captured.out
    assert "\x1b[" not in captured.out
    assert "\x1b[" not in captured.err


def test_simple_cli_resolves_collision_from_tilesets_json(
    tmp_path: Path,
    capsys,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_B.png",
        color=(0, 255, 0, 255),
    )

    create_tilesets_json(input_directory)

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    content = (output_directory / "Inside.tres").read_text(
        encoding="utf-8",
    )

    # Three of the four B tiles are flagged as blocking movement.
    assert content.count("/physics_layer_0/polygon_0/points") == 3
    assert "physics_layer_0/collision_layer = 1" in content

    captured = capsys.readouterr()

    assert "[2/4] Resolving collision flags" in captured.out
    assert "Resolved collision from Tilesets.json" in captured.out


def test_simple_cli_without_tilesets_json_stays_collision_free(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_B.png",
        color=(0, 255, 0, 255),
    )

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    content = (output_directory / "Inside.tres").read_text(
        encoding="utf-8",
    )

    assert "/physics_layer_0/polygon" not in content


def flatten(text: str) -> str:
    """Collapse whitespace runs — panels wrap long lines."""
    return " ".join(text.split())


def test_missing_arguments_show_banner_then_usage_panel(
    capsys,
) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    output = flatten(captured.out)

    assert exit_code == 2

    # The startup banner is displayed first, like any regular run.
    assert "rpgmaker2godot v0.1.0" in output
    assert (
        "Convert RPG Maker MV/MZ tilesets to Godot resources."
        in output
    )

    # The usage failure follows, rendered inside a warning frame.
    assert (
        "usage: rpgmaker2godot [-h] [--simple] input output"
        in output
    )
    assert (
        "rpgmaker2godot: error: the following arguments are "
        "required: input, output" in output
    )
    assert "┌" in captured.out
    assert "└" in captured.out


def test_unrecognized_arguments_report_usage(
    tmp_path: Path,
    capsys,
) -> None:
    # Valid positionals plus an unknown option: argparse only
    # reports unrecognized arguments once required ones are filled.
    exit_code = main(
        [
            str(tmp_path),
            str(tmp_path / "output"),
            "--bogus",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert (
        "rpgmaker2godot: error: unrecognized arguments: --bogus"
        in flatten(captured.out)
    )


def test_missing_simple_flag_reports_usage(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(
        [
            str(tmp_path),
            str(tmp_path / "output"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert (
        "rpgmaker2godot: error: Only --simple mode is currently "
        "supported." in flatten(captured.out)
    )


def project_log_file() -> Path:
    """Path of the developer-facing log at the repository root."""

    return Path(__file__).resolve().parents[1] / "rpgmaker2godot.log"


def test_error_runs_never_record_into_any_log_file(capsys) -> None:
    """An argument failure must not produce a single log record."""

    project_log = project_log_file()
    before = project_log.read_bytes() if project_log.exists() else None

    # An aggressive configuration sits in the current (sandboxed) working
    # directory: even so, the failure path must not write anything.
    working_directory = Path.cwd()
    (working_directory / "logging.json").write_text(
        json.dumps(
            {
                "enabled": True,
                "level": "DEBUG",
                "file": str(working_directory / "probe.log"),
                "mode": "APPEND",
            },
        ),
        encoding="utf-8",
    )

    exit_code = main([])
    capsys.readouterr()

    assert exit_code == 2

    probe = working_directory / "probe.log"

    assert not probe.exists() or probe.stat().st_size == 0

    if before is not None:
        assert project_log.read_bytes() == before


def test_conversion_records_stay_inside_the_test_sandbox(
    tmp_path: Path,
    capsys,
) -> None:
    """Debug records go to the sandbox only, never to the project log."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_B.png",
        color=(0, 255, 0, 255),
    )

    # With a Tilesets.json present the resolver fires and produces the
    # per-tile debug records the probe must capture.
    create_tilesets_json(input_directory)

    project_log = project_log_file()
    before = project_log.read_bytes() if project_log.exists() else None

    working_directory = Path.cwd()
    (working_directory / "logging.json").write_text(
        json.dumps(
            {
                "enabled": True,
                "level": "DEBUG",
                "file": str(working_directory / "probe.log"),
                "mode": "OVERWRITE",
            },
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--simple",
            str(input_directory),
            str(output_directory),
        ]
    )
    capsys.readouterr()

    assert exit_code == 0

    # Records were produced… inside the sandbox probe exclusively.
    probe = working_directory / "probe.log"
    assert probe.exists()
    assert "resolve Inside" in probe.read_text(encoding="utf-8")

    # …and the project log at the repository root stayed untouched.
    if before is not None:
        assert project_log.read_bytes() == before