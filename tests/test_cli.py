import json
from pathlib import Path

import yaml
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


def test_simple_cli_no_merge_exports_one_file_per_sheet(
    tmp_path: Path,
) -> None:
    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    for filename, color in (
        ("Inside_A5.png", (255, 0, 0, 255)),
        ("Inside_B.png", (0, 255, 0, 255)),
        ("Inside_C.png", (0, 0, 255, 255)),
    ):
        create_sheet(
            input_directory,
            filename,
            color=color,
        )

    exit_code = main(
        [
            "--simple",
            "--no-merge",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    # The default behaviour stacks the three sheets in a single
    # Inside atlas. With --no-merge each sheet stays separate.
    assert not (output_directory / "Inside.png").exists()

    for stem in ("Inside_A5", "Inside_B", "Inside_C"):
        atlas_path = output_directory / f"{stem}.png"
        resource_path = output_directory / f"{stem}.tres"

        assert atlas_path.exists()
        assert resource_path.exists()

        with Image.open(atlas_path) as image:
            assert image.size == (96, 96)


def test_simple_cli_no_merge_resolves_collision_from_tilesets_json(
    tmp_path: Path,
    capsys,
) -> None:
    # Regression: --no-merge names the output tileset after the sheet
    # (Inside_A5) but collision lookup must still resolve the RPG tileset
    # by its prefix (Inside). Otherwise conversion aborts with
    # "Unknown RPG Maker tileset: 'Inside_A5'".
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

    # Flags array long enough to cover A5 global tile IDs (base 1536)
    # so the resolver never trips the out-of-range guard.
    data = [
        None,
        {
            "id": 1,
            "name": "Inside",
            "flags": [0x0000] * 2048,
        },
    ]

    (input_directory / "Tilesets.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--simple",
            "--no-merge",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()

    assert "Inside_A5.png" in captured.out
    assert "Inside_B.png" in captured.out
    assert "Unknown RPG Maker tileset" not in captured.out
    assert "Unknown RPG Maker tileset" not in captured.err

    # Collision was resolved (the resolver ran) without aborting.
    assert (output_directory / "Inside_A5.tres").exists()
    assert (output_directory / "Inside_B.tres").exists()


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

    # Panel borders sit between wrapped lines: strip them before
    # flattening so the (long) usage line can be matched contiguously.
    output = flatten(captured.out.replace("│", " "))

    assert exit_code == 2

    # The startup banner is displayed first, like any regular run.
    assert "rpgmaker2godot v0.1.0" in output
    assert (
        "Convert RPG Maker MV/MZ tilesets to Godot resources."
        in output
    )

    # The usage failure follows, rendered inside a warning frame.
    assert (
        "usage: rpgmaker2godot [-h] [--mode {TILESET,CHARACTER}] [--simple] [--tileset TILESET] [--no-merge] [--tolerance TOLERANCE] [--no-terrains] input output"
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
    (working_directory / "rpgmaker2godot.yaml").write_text(
        yaml.safe_dump(
            {
                "logger": {
                    "enabled": True,
                    "level": "DEBUG",
                    "file": str(working_directory / "probe.log"),
                    "mode": "APPEND",
                },
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
    (working_directory / "rpgmaker2godot.yaml").write_text(
        yaml.safe_dump(
            {
                "logger": {
                    "enabled": True,
                    "level": "DEBUG",
                    "file": str(working_directory / "probe.log"),
                    "mode": "OVERWRITE",
                },
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


def test_tolerance_option_merges_noisy_a4_tiles(
    tmp_path: Path,
    capsys,
) -> None:
    """--tolerance N merges A4 tiles differing by at most N pixels.

    A uniform A4 sheet with one stray pixel produces two exact-unique
    tiles; running again with --tolerance 1 collapses them into the
    first occurrence.
    """

    input_directory = tmp_path / "tilesets"

    create_sheet(
        input_directory,
        "Inside_A4.png",
        size=(768, 720),
        color=(90, 90, 90, 255),
    )

    with Image.open(input_directory / "Inside_A4.png") as image:
        sheet = image.convert("RGBA")

    sheet.putpixel((5, 5), (255, 0, 0, 255))
    sheet.save(input_directory / "Inside_A4.png")
    sheet.close()

    default_exit = main(
        [
            "--simple",
            "--no-merge",
            str(input_directory),
            str(tmp_path / "default"),
        ]
    )

    assert default_exit == 0

    default_output = capsys.readouterr().out
    assert "Inside_A4: 2 tiles from 1 sheet" in default_output

    tolerant_exit = main(
        [
            "--simple",
            "--no-merge",
            "--tolerance",
            "1",
            str(input_directory),
            str(tmp_path / "tolerant"),
        ]
    )

    assert tolerant_exit == 0

    tolerant_output = capsys.readouterr().out
    assert "Inside_A4: 1 tile from 1 sheet" in tolerant_output

    with Image.open(tmp_path / "tolerant" / "Inside_A4.png") as image:
        assert image.size == (768, 48)


def test_negative_tolerance_reports_usage(
    tmp_path: Path,
    capsys,
) -> None:
    """A negative --tolerance is a usage error (exit code 2)."""

    exit_code = main(
        [
            "--simple",
            "--tolerance",
            "-1",
            str(tmp_path),
            str(tmp_path / "output"),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--tolerance must be >= 0." in flatten(captured.out)


def test_no_terrains_flag_skips_terrain_generation(
    tmp_path: Path,
) -> None:
    """--no-terrains omits the terrain metadata from the .tres."""

    input_directory = tmp_path / "tilesets"

    create_sheet(
        input_directory,
        "Inside_A4.png",
        size=(768, 720),
    )

    default_exit = main(
        [
            "--simple",
            "--no-merge",
            str(input_directory),
            str(tmp_path / "default"),
        ]
    )

    assert default_exit == 0

    default_content = (
        tmp_path / "default" / "Inside_A4.tres"
    ).read_text(encoding="utf-8")

    assert "terrain_set_0/mode = 0" in default_content
    assert 'terrain_set_0/terrain_0/name = "Wall top 1"' in default_content
    assert "0:0/0/terrains_peering_bit/" in default_content

    skipped_exit = main(
        [
            "--simple",
            "--no-merge",
            "--no-terrains",
            str(input_directory),
            str(tmp_path / "skipped"),
        ]
    )

    assert skipped_exit == 0

    skipped_content = (
        tmp_path / "skipped" / "Inside_A4.tres"
    ).read_text(encoding="utf-8")

    assert "terrain_set_0/mode" not in skipped_content
    assert "terrains_peering_bit" not in skipped_content


def test_tileset_option_converts_only_named_tileset(
    tmp_path: Path,
) -> None:
    """--tileset Outside converts the Outside family only."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    for tileset, color in (
        ("Inside", (255, 0, 0, 255)),
        ("Outside", (0, 255, 0, 255)),
    ):
        for sheet_type in ("A5", "B", "C"):
            create_sheet(
                input_directory,
                f"{tileset}_{sheet_type}.png",
                color=color,
            )

    exit_code = main(
        [
            "--simple",
            "--tileset",
            "Outside",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    # Only the requested tileset family is exported.
    assert (output_directory / "Outside.png").exists()
    assert (output_directory / "Outside.tres").exists()
    assert not (output_directory / "Inside.png").exists()
    assert not (output_directory / "Inside.tres").exists()


def test_tileset_option_accepts_png_extension(
    tmp_path: Path,
) -> None:
    """--tileset Outside.png resolves to the Outside family."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    for tileset in ("Inside", "Outside"):
        for sheet_type in ("A5", "B", "C"):
            create_sheet(
                input_directory,
                f"{tileset}_{sheet_type}.png",
            )

    exit_code = main(
        [
            "--simple",
            "--tileset",
            "Outside.png",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    assert (output_directory / "Outside.png").exists()
    assert not (output_directory / "Inside.png").exists()


def test_tileset_option_single_sheet_file(
    tmp_path: Path,
) -> None:
    """--tileset Inside_B.png converts exactly that one sheet."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    for sheet_type in ("A5", "B", "C"):
        create_sheet(
            input_directory,
            f"Inside_{sheet_type}.png",
        )

    exit_code = main(
        [
            "--simple",
            "--no-merge",
            "--tileset",
            "Inside_B.png",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    assert (output_directory / "Inside_B.png").exists()
    assert (output_directory / "Inside_B.tres").exists()
    assert not (output_directory / "Inside_A5.png").exists()
    assert not (output_directory / "Inside_C.png").exists()


def test_tileset_option_defaults_to_png_extension(
    tmp_path: Path,
) -> None:
    """--tileset Inside_B (no extension) finds Inside_B.png."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    for sheet_type in ("A5", "B", "C"):
        create_sheet(
            input_directory,
            f"Inside_{sheet_type}.png",
        )

    exit_code = main(
        [
            "--simple",
            "--no-merge",
            "--tileset",
            "Inside_B",
            str(input_directory),
            str(output_directory),
        ]
    )

    assert exit_code == 0

    assert (output_directory / "Inside_B.png").exists()
    assert (output_directory / "Inside_B.tres").exists()
    assert not (output_directory / "Inside_A5.png").exists()


def test_missing_tileset_displays_warning(
    tmp_path: Path,
    capsys,
) -> None:
    """--tileset Ghost warns and converts nothing (exit code 1)."""

    input_directory = tmp_path / "tilesets"
    output_directory = tmp_path / "output"

    create_sheet(
        input_directory,
        "Inside_B.png",
    )

    exit_code = main(
        [
            "--simple",
            "--tileset",
            "Ghost",
            str(input_directory),
            str(output_directory),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1

    # The warning is rendered in the same warning panel as usage
    # failures; panels wrap long lines, so flatten the output.
    output = flatten(captured.out.replace("│", " "))

    assert "Tileset 'Ghost' not found" in output
    assert "Nothing was converted" in output

    # The message sits inside a warning panel frame.
    assert "┌" in captured.out
    assert "└" in captured.out

    # No output was generated for the missing tileset.
    assert not output_directory.exists()


def test_tileset_output_path_comes_from_the_configuration(
    tmp_path: Path,
) -> None:
    """tileset.path in rpgmaker2godot.yaml drives the res:// reference."""

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

    # The conftest runs every test in a fresh working directory:
    # dropping rpgmaker2godot.yaml there mirrors a real run.
    working_directory = Path.cwd()
    (working_directory / "rpgmaker2godot.yaml").write_text(
        yaml.safe_dump(
            {
                "tileset": {
                    "path": "world/tilesets",
                },
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

    assert exit_code == 0

    content = (output_directory / "Inside.tres").read_text(
        encoding="utf-8",
    )

    assert 'path="res://world/tilesets/Inside.png"' in content