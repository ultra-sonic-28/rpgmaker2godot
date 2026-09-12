"""Unit tests of the cli_helper rendering and plumbing helpers.

The two pipeline functions (``_run_character_mode`` and
``_run_tileset_mode``) are exercised end-to-end by the CLI tests
(``test_cli.py`` / ``test_character_cli.py``) through ``main``; only
the standalone helpers are tested here.
"""

import argparse
import io
from pathlib import Path

import pytest

from rpgmaker2godot.analysis.models import (
    AnalysisResult,
    RPGMakerVersion,
    SheetInfo,
)
from rpgmaker2godot.character.layout import CHARACTER_ANIMATION_FAMILIES
from rpgmaker2godot.cli_helper import (
    _character_animation_overrides,
    _format_usage_error,
    _join_terrain_names,
    _paint,
    _Parser,
    _print_step,
    _print_terrain_resolution,
    _select_tileset,
    _supports_colors,
    _UsageError,
    _warn_ignored_tileset_options,
)
from rpgmaker2godot.godot.model import GodotTerrain, GodotTerrainSet
from rpgmaker2godot.godot.terrain.terrain_builder import TerrainResolution
from rpgmaker2godot.model import SheetType
from rpgmaker2godot.utils.config import (
    AnimationConfig,
    AppConfig,
    CharacterConfig,
)


class FakeTty:
    """A stream pretending to be a terminal (``isatty`` -> True)."""

    def isatty(self) -> bool:
        return True


def make_sheet(
    prefix: str,
    sheet_type: SheetType,
) -> SheetInfo:
    """Build one detected sheet info for the given prefix and type."""

    return SheetInfo(
        sheet_type=sheet_type,
        path=Path(f"{prefix}_{sheet_type.value}.png"),
        prefix=prefix,
        width=96,
        height=96,
        tile_width=48,
        tile_height=48,
        columns=2,
        rows=2,
    )


def make_result(
    directory: Path,
    *sheets: SheetInfo,
) -> AnalysisResult:
    """Build an analysis result carrying the given sheets."""

    return AnalysisResult(
        input_directory=directory,
        version=RPGMakerVersion.UNKNOWN,
        tile_width=48,
        tile_height=48,
        sheets=tuple(sheets),
        warnings=(),
    )


def make_resolution(
    *terrain_set_names: str,
) -> TerrainResolution:
    """Build a terrain resolution carrying one set per given name."""

    terrain_sets = tuple(
        GodotTerrainSet(
            mode=0,
            terrains=(GodotTerrain(name=name, color=(1.0, 0.0, 0.0)),),
        )
        for name in terrain_set_names
    )

    return TerrainResolution(
        terrain_sets=terrain_sets,
        kind_assignment={},
    )


def test_usage_error_carries_usage_and_message() -> None:
    error = _UsageError("usage: rpgmaker2godot", "something failed")

    assert str(error) == "something failed"
    assert error.usage == "usage: rpgmaker2godot"
    assert error.message == "something failed"


def test_parser_error_raises_a_usage_error() -> None:
    parser = _Parser(prog="rpgmaker2godot")

    with pytest.raises(_UsageError) as caught:
        parser.error("unrecognized arguments: --bogus")

    assert caught.value.message == "unrecognized arguments: --bogus"

    # The usage text is stored verbatim: the trailing newline is
    # stripped later, when _format_usage_error renders the panel.
    assert caught.value.usage == parser.format_usage()


def test_supports_colors_is_disabled_by_no_color(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)

    assert _supports_colors(FakeTty()) is False


def test_supports_colors_is_forced_by_force_color(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")

    assert _supports_colors(io.StringIO()) is True


def test_supports_colors_follows_the_stream(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)

    assert _supports_colors(io.StringIO()) is False
    assert _supports_colors(FakeTty()) is True


def test_paint_is_plain_on_a_redirected_stream() -> None:
    assert _paint("hello", "97;44", io.StringIO()) == "hello"


def test_paint_wraps_the_text_in_ansi_colors() -> None:
    painted = _paint("hello", "97;44", FakeTty())

    assert painted == "\x1b[97;44mhello\x1b[0m"


def test_paint_stays_plain_with_no_color(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")

    assert _paint("hello", "97;44", FakeTty()) == "hello"


def test_print_step_writes_a_numbered_heading(capsys) -> None:
    _print_step(2, "Converting tiles", 5)

    captured = capsys.readouterr()

    # A blank line separates the step heading from the previous block.
    assert captured.out.startswith("\n")
    assert "[2/5] Converting tiles" in captured.out


def test_print_step_stays_plain_when_redirected(monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("NO_COLOR", "1")

    _print_step(1, "Analyzing input directory", 5)

    captured = capsys.readouterr()

    assert "[1/5] Analyzing input directory" in captured.out
    assert "\x1b[" not in captured.out


def test_join_terrain_names_keeps_a_short_list_whole() -> None:
    assert _join_terrain_names(["Ground 1", "Water 1"]) == "Ground 1, Water 1"


def test_join_terrain_names_truncates_a_long_list() -> None:
    names = [f"Terrain {index}" for index in range(1, 10)]

    joined = _join_terrain_names(names)

    # Only the first six names are kept, the remainder summarized.
    assert joined == (
        "Terrain 1, Terrain 2, Terrain 3, Terrain 4, Terrain 5, "
        "Terrain 6, … (+3)"
    )


def test_join_terrain_names_handles_exactly_the_limit() -> None:
    names = [f"Terrain {index}" for index in range(1, 7)]

    assert _join_terrain_names(names) == ", ".join(names)


def test_print_terrain_resolution_without_terrain_sets(capsys) -> None:
    _print_terrain_resolution("Inside", make_resolution())

    captured = capsys.readouterr()

    assert (
        "  Inside: no terrain sets (no A1/A2/A3/A4 autotiles)"
        in captured.out
    )


def test_print_terrain_resolution_with_one_set(capsys) -> None:
    _print_terrain_resolution("Inside", make_resolution("Ground 1"))

    captured = capsys.readouterr()

    assert "  Inside: 1 terrain set (Ground 1)" in captured.out


def test_print_terrain_resolution_with_several_sets(capsys) -> None:
    resolution = make_resolution(
        "Ground 1",
        "Water 1",
        "Waterfall 1",
        "Roof 1",
        "Wall 1",
        "Wall top 1",
        "Wall side 1",
    )

    _print_terrain_resolution("Inside", resolution)

    captured = capsys.readouterr()

    # The singular/plural wording is right and the long list is
    # summarized through _join_terrain_names.
    assert "  Inside: 7 terrain sets (" in captured.out
    assert "… (+1)" in captured.out


def test_format_usage_error_mirrors_argparse() -> None:
    parser = _Parser(prog="rpgmaker2godot")

    rendered = _format_usage_error(parser, "something is wrong")

    assert rendered == (
        f"{parser.format_usage().rstrip(chr(10))}\n"
        "rpgmaker2godot: error: something is wrong"
    )


def test_select_tileset_matches_a_single_sheet_file(tmp_path: Path) -> None:
    sheets = (
        make_sheet("Inside", SheetType.A5),
        make_sheet("Inside", SheetType.B),
        make_sheet("Outside", SheetType.B),
    )
    result = make_result(tmp_path, *sheets)

    selected, warning = _select_tileset(result, "Inside_B")

    assert warning is None
    assert len(selected.sheets) == 1
    assert selected.sheets[0].sheet_type == SheetType.B
    assert selected.sheets[0].prefix == "Inside"

    # The original frozen result is untouched.
    assert len(result.sheets) == 3


def test_select_tileset_assumes_the_png_extension(tmp_path: Path) -> None:
    result = make_result(
        tmp_path,
        make_sheet("Inside", SheetType.B),
    )

    selected, warning = _select_tileset(result, "Inside_B.png")

    assert warning is None
    assert len(selected.sheets) == 1


def test_select_tileset_matches_a_family_by_prefix(tmp_path: Path) -> None:
    sheets = (
        make_sheet("Inside", SheetType.A5),
        make_sheet("Inside", SheetType.B),
        make_sheet("Outside", SheetType.B),
    )
    result = make_result(tmp_path, *sheets)

    selected, warning = _select_tileset(result, "Inside")

    assert warning is None
    assert len(selected.sheets) == 2
    assert all(sheet.prefix == "Inside" for sheet in selected.sheets)


def test_select_tileset_matching_is_case_insensitive(
    tmp_path: Path,
) -> None:
    result = make_result(
        tmp_path,
        make_sheet("Inside", SheetType.B),
    )

    selected, warning = _select_tileset(result, "INSIDE_b")

    assert warning is None
    assert len(selected.sheets) == 1


def test_select_tileset_reports_an_unknown_request(
    tmp_path: Path,
) -> None:
    result = make_result(
        tmp_path,
        make_sheet("Inside", SheetType.B),
    )

    selected, warning = _select_tileset(result, "Ghost")

    # The untouched result is returned together with the warning.
    assert len(selected.sheets) == 1
    assert warning is not None
    assert "Tileset 'Ghost' not found" in warning
    assert "no sheet named 'Ghost.png'" in warning
    assert "no tileset prefix 'Ghost_'" in warning
    assert "Nothing was converted." in warning


@pytest.mark.parametrize(
    "attributes,expected",
    [
        ({}, None),
        ({"tileset": "Inside_B"}, ["--tileset"]),
        ({"no_merge": True}, ["--no-merge"]),
        ({"no_terrains": True}, ["--no-terrains"]),
        ({"tolerance": 4}, ["--tolerance"]),
        (
            {"tileset": "Inside_B", "no_merge": True, "tolerance": 4},
            ["--tileset", "--no-merge", "--tolerance"],
        ),
    ],
)
def test_warn_ignored_tileset_options(
    attributes: dict,
    expected: list[str] | None,
    capsys,
) -> None:
    defaults = {
        "tileset": None,
        "no_merge": False,
        "no_terrains": False,
        "tolerance": 0,
    }

    args = argparse.Namespace(**{**defaults, **attributes})

    _warn_ignored_tileset_options(args)

    captured = capsys.readouterr()

    if not expected:
        assert captured.err == ""
        return

    # The ignored option(s) are listed on stderr, singular or plural.
    plural = "s" if len(expected) > 1 else ""
    joined = " ".join(expected)

    assert (
        f"Tileset-only option{plural} {joined} ignored "
        f"in --mode CHARACTER." in captured.err
    )


def test_character_animation_overrides_covers_every_animation() -> None:
    config = AppConfig(
        character=CharacterConfig(
            idle=AnimationConfig(speed=3.0, duration=0.5, loop=True),
            walk=AnimationConfig(speed=6.0, duration=1.0, loop=True),
            damaged=AnimationConfig(speed=5.0, duration=2.0, loop=False),
        ),
    )

    overrides = _character_animation_overrides(config)

    expected_names = {
        name
        for names in CHARACTER_ANIMATION_FAMILIES.values()
        for name in names
    }

    assert set(overrides) == expected_names

    # Every idle-down…idle-up animation shares the idle playback
    # settings, and the damaged animation carries its own.
    assert overrides["idle-down"] == (3.0, 0.5, True)
    assert overrides["idle-up"] == (3.0, 0.5, True)
    assert overrides["walk-left"] == (6.0, 1.0, True)
    assert overrides["damaged"] == (5.0, 2.0, False)
