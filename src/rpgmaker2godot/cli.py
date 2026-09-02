import argparse
import os
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import TextIO

from PIL import Image

from .analysis.character_detector import CharacterDetector
from .analysis.detector import TilesetDetector
from .analysis.models import AnalysisResult
from .character.layout import CHARACTER_ANIMATION_FAMILIES
from .character.spritesheet_builder import CharacterSpriteSheetBuilder
from .conversion.converter import SimpleConverter
from .godot.export.characters import CharacterExporter
from .godot.export.simple import SimpleExporter
from .godot.terrain.terrain_builder import (
    GodotTerrainBuilder,
    TerrainResolution,
)
from .tileset.reader import TilesetsJsonReader
from .tileset.resolver import TilePropertiesResolver
from .utils.config import AppConfig, load_app_config
from .utils.log import configure_logging
from .utils.messages import display_program_banner, display_warning

TILESET_TOTAL_STEPS = 5
CHARACTER_TOTAL_STEPS = 3

_RESET = "\x1b[0m"

_STEP_STYLE = "97;44"           # white on blue
_WARNING_STYLE = "97;48;5;208"  # white on orange (256-color)
_ERROR_STYLE = "97;41"          # white on red
_SUCCESS_STYLE = "97;42"        # white on green


class _UsageError(Exception):
    """Argument parsing failure carrying its formatted usage text."""

    def __init__(
        self,
        usage: str,
        message: str,
    ) -> None:
        super().__init__(message)

        self.usage = usage
        self.message = message


class _Parser(argparse.ArgumentParser):
    """Argument parser raising catchable errors instead of exiting.

    argparse terminates the process straight from ``error()``;
    raising instead lets ``main`` render failures through the
    standard warning UI while keeping the process exit code (2).
    """

    def error(
        self,
        message: str,
    ) -> None:
        raise _UsageError(self.format_usage(), message)


def _supports_colors(
    stream: TextIO,
) -> bool:
    """Return whether the stream should receive ANSI colors.

    Colors are disabled when the output is redirected (pipes,
    CI logs, test captures) unless FORCE_COLOR is set, and can
    be forced off with the standard NO_COLOR convention.
    """

    if os.environ.get("NO_COLOR"):
        return False

    if os.environ.get("FORCE_COLOR"):
        return True

    return (
        hasattr(stream, "isatty")
        and stream.isatty()
    )


def _paint(
    text: str,
    attributes: str,
    stream: TextIO,
) -> str:
    """Wrap text in ANSI colors when the stream supports them."""

    if not _supports_colors(stream):
        return text

    return f"\x1b[{attributes}m{text}{_RESET}"


def _print_step(
    step: int,
    label: str,
    total: int,
) -> None:
    """Print a numbered pipeline step heading."""

    print()
    print(
        _paint(
            f"[{step}/{total}] {label}",
            _STEP_STYLE,
            sys.stdout,
        )
    )


# Maximum number of terrain-set names kept on the "[4/5] Resolving terrain
# definitions" detail line; the remainder is summarized so a fully-drawn
# A4 sheet never produces a single, unboundedly long line.
_MAX_TERRAIN_NAMES = 6


def _join_terrain_names(names: list[str]) -> str:
    """Render a bounded, human-readable list of terrain-set names."""

    if len(names) <= _MAX_TERRAIN_NAMES:
        return ", ".join(names)

    shown = names[:_MAX_TERRAIN_NAMES]
    remaining = len(names) - _MAX_TERRAIN_NAMES

    return ", ".join(shown) + f", … (+{remaining})"


def _print_terrain_resolution(
    tileset_name: str,
    resolution: TerrainResolution,
) -> None:
    """Print one indented detail line for a resolved tileset."""

    set_count = len(resolution.terrain_sets)

    if set_count == 0:
        print(f"  {tileset_name}: no terrain sets (no A4 autotiles)")
        return

    names = _join_terrain_names(
        [
            terrain_set.terrains[0].name
            for terrain_set in resolution.terrain_sets
        ]
    )

    set_word = "terrain set" if set_count == 1 else "terrain sets"
    print(f"  {tileset_name}: {set_count} {set_word} ({names})")


def _format_usage_error(
    parser: argparse.ArgumentParser,
    message: str,
) -> str:
    """Render a parsing failure the way argparse would print it."""

    usage = parser.format_usage().rstrip("\n")

    return f"{usage}\n{parser.prog}: error: {message}"


def _select_tileset(
    result: AnalysisResult,
    requested: str,
) -> tuple[AnalysisResult, str | None]:
    """Restrict an analysis result to the requested tileset.

    The value names either a single sheet file (``Inside_B`` or
    ``Inside_B.png`` — the ``.png`` extension is assumed when
    omitted) or a tileset family by prefix (``Inside`` converts
    ``Inside_A4.png``, ``Inside_B.png``, ...).

    Matching is case-insensitive, like the detector's filename
    scan.

    Returns the filtered result, or the untouched result plus a
    warning message when nothing matches the request.
    """

    filename = (
        requested
        if requested.lower().endswith(".png")
        else f"{requested}.png"
    )

    name = filename[: -len(".png")]

    # A value naming an existing sheet file converts exactly that
    # sheet.
    selected = tuple(
        sheet
        for sheet in result.sheets
        if sheet.path.name.lower() == filename.lower()
    )

    if not selected:
        # Otherwise the value is a tileset name (the sheet filename
        # prefix): convert every sheet of that family.
        selected = tuple(
            sheet
            for sheet in result.sheets
            if sheet.prefix.lower() == name.lower()
        )

    if not selected:
        return result, (
            f"Tileset '{requested}' not found: no sheet named "
            f"'{filename}' and no tileset prefix '{name}_' in "
            f"{result.input_directory}. Nothing was converted."
        )

    return replace(result, sheets=selected), None


def _warn_ignored_tileset_options(
    args: argparse.Namespace,
) -> None:
    """Warn that tileset-only options have no effect in CHARACTER mode."""

    ignored = [
        option
        for option, enabled in (
            ("--tileset", args.tileset is not None),
            ("--no-merge", args.no_merge),
            ("--no-terrains", args.no_terrains),
            ("--tolerance", args.tolerance != 0),
        )
        if enabled
    ]

    if not ignored:
        return

    plural = "s" if len(ignored) > 1 else ""

    message = (
        f"Tileset-only option{plural} "
        f"{' '.join(ignored)} ignored in --mode CHARACTER."
    )

    print(
        f"  {_paint(message, _WARNING_STYLE, sys.stderr)}",
        file=sys.stderr,
    )


def _character_animation_overrides(
    config: AppConfig,
) -> dict[str, tuple[float, float, bool]]:
    """Per-animation playback overrides derived from the character config."""

    overrides: dict[str, tuple[float, float, bool]] = {}

    for family, names in CHARACTER_ANIMATION_FAMILIES.items():
        animation = getattr(config.character, family)

        for name in names:
            overrides[name] = (
                animation.speed,
                animation.duration,
                animation.loop,
            )

    return overrides


def _run_character_mode(
    args: argparse.Namespace,
    config: AppConfig,
) -> int:
    """Convert every character spritesheet of the input directory."""

    detector = CharacterDetector()
    result = detector.analyze(args.input)

    _print_step(
        1,
        "Analyzing input directory",
        CHARACTER_TOTAL_STEPS,
    )

    print(f"Input: {result.input_directory}")
    print()
    print("Sheets:")

    for sheet_info in result.sheets:
        print(
            f"  {sheet_info.path.name}  "
            f"{sheet_info.width}x{sheet_info.height}  "
            f"({sheet_info.frame_width}x{sheet_info.frame_height} frames)"
        )

    if result.warnings:
        print()
        print("Warnings:")

        for warning in result.warnings:
            print(
                f"  - {_paint(warning, _WARNING_STYLE, sys.stdout)}"
            )

    _print_step(
        2,
        "Building sprite frames",
        CHARACTER_TOTAL_STEPS,
    )

    conversion = CharacterSpriteSheetBuilder(
        animation_overrides=_character_animation_overrides(config),
    ).convert(result)

    for sheet in conversion.sheets:
        print(
            f"  {sheet.name}: {len(sheet.animations)} animations, "
            f"{sheet.frame_count} frames"
        )

    _print_step(
        3,
        "Exporting Godot resources",
        CHARACTER_TOTAL_STEPS,
    )

    exporter = CharacterExporter(
        godot_output_path=(config.character.path or None),
    )
    generated = exporter.export(
        conversion,
        args.output,
    )

    for sheet in conversion.sheets:
        print(
            f"  {sheet.name}.png   "
            f"{sheet.width}x{sheet.height} px "
            f"({sheet.frame_width}x{sheet.frame_height} frames)"
        )
        print(
            f"  {sheet.name}.tres  "
            f"{len(sheet.animations)} animations "
            f"({sheet.frame_count} frames)"
        )

    print()
    print(
        _paint("Generated:", _SUCCESS_STYLE, sys.stdout)
    )

    for path in generated:
        print(f"  {path.name}")

    return 0


def _run_tileset_mode(
    args: argparse.Namespace,
    config: AppConfig,
) -> int:
    """Convert every (or the selected) tileset of the input directory."""

    detector = TilesetDetector()
    result = detector.analyze(args.input)

    if args.tileset is not None:
        result, warning = _select_tileset(
            result,
            args.tileset,
        )

        if warning is not None:
            display_warning(warning)

            return 1

    _print_step(1, "Analyzing input directory", TILESET_TOTAL_STEPS)

    print(f"Input: {result.input_directory}")
    print(f"Tile size: {result.tile_width}x{result.tile_height}")
    print()
    print("Sheets:")

    groups: dict[str, list] = defaultdict(list)

    for sheet in result.sheets:
        groups[sheet.prefix].append(sheet)

    for prefix, sheets in sorted(groups.items()):
        print()
        print(f"  {prefix or '(no prefix)'}")

        for sheet in sorted(
            sheets,
            key=lambda sheet: sheet.sheet_type.order,
        ):
            print(
                f"    {sheet.sheet_type.value}.png "
                f"{sheet.width:>4}x{sheet.height:<4} "
                f"({sheet.columns}x{sheet.rows} tiles)"
            )

    if result.warnings:
        print()
        print("Warnings:")

        for warning in result.warnings:
            print(
                f"  - {_paint(warning, _WARNING_STYLE, sys.stdout)}"
            )

    _print_step(2, "Resolving collision flags", TILESET_TOTAL_STEPS)

    tilesets_json_path = args.input / "Tilesets.json"

    if tilesets_json_path.is_file():
        tileset_flags = TilesetsJsonReader().read_flags(
            tilesets_json_path,
        )

        converter = SimpleConverter(
            tile_properties_resolver=(
                TilePropertiesResolver(
                    {
                        flags.name: flags
                        for flags in tileset_flags
                    }
                )
            ),
            no_merge=args.no_merge,
            a4_pixel_tolerance=args.tolerance,
        )

        print(
            f"  Resolved collision from {tilesets_json_path.name}"
        )
    else:
        print(
            f"  {_paint('Tilesets.json not found: generated tiles will have no collision.', _WARNING_STYLE, sys.stderr)}",
            file=sys.stderr,
        )

        converter = SimpleConverter(
            no_merge=args.no_merge,
            a4_pixel_tolerance=args.tolerance,
        )

    _print_step(3, "Converting tiles", TILESET_TOTAL_STEPS)

    conversion = converter.convert(result)

    for tileset in conversion.tilesets:
        tile_count = sum(
            len(sheet.tiles)
            for sheet in tileset.sheets
        )

        sheet_count = len(tileset.sheets)
        tile_word = "tile" if tile_count == 1 else "tiles"
        sheet_word = "sheet" if sheet_count == 1 else "sheets"

        print(
            f"  {tileset.name}: "
            f"{tile_count} {tile_word} from "
            f"{sheet_count} {sheet_word}"
        )

    _print_step(4, "Resolving terrain definitions", TILESET_TOTAL_STEPS)

    terrain_plans: dict[str, TerrainResolution] = {}

    if args.no_terrains:
        print("  Skipped (--no-terrains)")
    else:
        terrain_builder = GodotTerrainBuilder()

        for tileset in conversion.tilesets:
            resolution = terrain_builder.resolve(tileset)
            terrain_plans[tileset.name] = resolution

            _print_terrain_resolution(tileset.name, resolution)

    _print_step(5, "Exporting Godot resources", TILESET_TOTAL_STEPS)

    exporter = SimpleExporter(
        godot_output_path=(config.tileset.path or None),
        terrains=not args.no_terrains,
    )

    generated = exporter.export(
        conversion,
        args.output,
        terrain_resolutions=terrain_plans or None,
    )

    for tileset in conversion.tilesets:
        atlas_path = args.output / f"{tileset.name}.png"

        with Image.open(atlas_path) as image:
            width, height = image.size

        tile_width = tileset.sheets[0].tile_width
        tile_height = tileset.sheets[0].tile_height

        columns = width // tile_width
        rows = height // tile_height

        print(
            f"  {tileset.name}.png   "
            f"{width}x{height} px "
            f"({columns}x{rows} tiles)"
        )
        print(
            f"  {tileset.name}.tres  "
            f"{columns}x{rows} tiles"
        )

    print()
    print(
        _paint("Generated:", _SUCCESS_STYLE, sys.stdout)
    )

    for path in generated:
        print(f"  {path.name}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(
        prog="rpgmaker2godot",
        description="Convert RPG Maker MV/MZ tilesets to Godot resources.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input directory containing the files to convert.",
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Output directory.",
    )

    parser.add_argument(
        "--mode",
        type=str.upper,
        choices=("TILESET", "CHARACTER"),
        default="TILESET",
        help=(
            "Processing mode: TILESET converts RPG Maker tilesheets "
            "into Godot TileSet resources for maps (default), "
            "CHARACTER converts character spritesheets (player-1.png "
            "style files, NOT RPG Maker character sheets) into Godot "
            "SpriteFrames resources."
        ),
    )

    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use the simple conversion mode (A5/B/C/D/E).",
    )

    parser.add_argument(
        "--tileset",
        metavar="TILESET",
        default=None,
        help=(
            "TILESET mode only. Convert only the named tileset: "
            "either a single sheet file (e.g. Inside_B, the .png "
            "extension is assumed when omitted) or a tileset family "
            "by prefix (e.g. Inside converts every Inside_*.png "
            "sheet). When omitted, every tileset found in the input "
            "directory is converted."
        ),
    )

    parser.add_argument(
        "--no-merge",
        action="store_true",
        help=(
            "Keep the source sheet split: export one PNG atlas and one "
            ".tres per input sheet instead of grouping the sheets "
            "sharing a prefix into a single stacked output (default: "
            "merge)."
        ),
    )

    parser.add_argument(
        "--tolerance",
        type=int,
        default=0,
        help=(
            "Merge unfolded A4 tiles whose pixel difference is within "
            "N pixels, discarding source-image noise (default: 0, "
            "byte-exact match)."
        ),
    )

    parser.add_argument(
        "--no-terrains",
        action="store_true",
        help=(
            "Skip Godot terrain generation for the unfolded A4 "
            "autotiles (terrains power the automatic connection tool "
            "in the Godot editor)."
        ),
    )

    # Enable ANSI escape sequences on the legacy Windows console.
    os.system("")

    # Opt-in logging, activated by a rpgmaker2godot.yaml file in
    # the working directory.
    configure_logging()

    display_program_banner()

    try:
        args = parser.parse_args(argv)
    except _UsageError as error:
        display_warning(
            _format_usage_error(parser, error.message),
        )

        return 2

    character_mode = args.mode == "CHARACTER"

    if character_mode:
        if args.simple:
            display_warning(
                _format_usage_error(
                    parser,
                    "--simple applies to tileset conversion only.",
                ),
            )

            return 2

        _warn_ignored_tileset_options(args)

    else:
        if not args.simple:
            display_warning(
                _format_usage_error(
                    parser,
                    "Only --simple mode is currently supported.",
                ),
            )

            return 2

        if args.tolerance < 0:
            display_warning(
                _format_usage_error(
                    parser,
                    "--tolerance must be >= 0.",
                ),
            )

            return 2

    app_config = load_app_config()

    try:
        if character_mode:
            return _run_character_mode(args, app_config)

        return _run_tileset_mode(args, app_config)

    except (
        FileNotFoundError,
        NotADirectoryError,
        ValueError,
        IndexError,
    ) as error:
        print(
            _paint(f"Error: {error}", _ERROR_STYLE, sys.stderr),
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())