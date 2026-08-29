import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import TextIO

from PIL import Image

from .analysis.detector import TilesetDetector
from .conversion.converter import SimpleConverter
from .godot.export.simple import SimpleExporter
from .tileset.reader import TilesetsJsonReader
from .tileset.resolver import TilePropertiesResolver
from .utils.log import configure_logging
from .utils.messages import display_program_banner, display_warning

TOTAL_STEPS = 4

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
) -> None:
    """Print a numbered pipeline step heading."""

    print()
    print(
        _paint(
            f"[{step}/{TOTAL_STEPS}] {label}",
            _STEP_STYLE,
            sys.stdout,
        )
    )


def _format_usage_error(
    parser: argparse.ArgumentParser,
    message: str,
) -> str:
    """Render a parsing failure the way argparse would print it."""

    usage = parser.format_usage().rstrip("\n")

    return f"{usage}\n{parser.prog}: error: {message}"


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(
        prog="rpgmaker2godot",
        description="Convert RPG Maker MV/MZ tilesets to Godot resources.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input directory containing RPG Maker tilesheets.",
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Output directory.",
    )

    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use the simple conversion mode (A5/B/C/D/E).",
    )

    parser.add_argument(
        "--no-merge",
        action="store_true",
        help=(
            "Keep the source sheet split: export one PNG atlas and one "
            ".tres per input sheet instead of merging them into a single "
            "output (default: merge sheets sharing a prefix)."
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

    # Enable ANSI escape sequences on the legacy Windows console.
    os.system("")

    # Opt-in logging, activated by a logging.json file in the
    # working directory.
    configure_logging()

    display_program_banner()

    try:
        args = parser.parse_args(argv)
    except _UsageError as error:
        display_warning(
            _format_usage_error(parser, error.message),
        )

        return 2

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

    try:
        detector = TilesetDetector()
        result = detector.analyze(args.input)

        _print_step(1, "Analyzing input directory")

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

        _print_step(2, "Resolving collision flags")

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

        _print_step(3, "Converting tiles")

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

        _print_step(4, "Exporting Godot resources")

        exporter = SimpleExporter()
        generated = exporter.export(
            conversion,
            args.output,
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