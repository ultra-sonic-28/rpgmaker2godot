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
from .utils.messages import display_program_banner

TOTAL_STEPS = 4

_RESET = "\x1b[0m"

_STEP_STYLE = "97;44"           # white on blue
_WARNING_STYLE = "97;48;5;208"  # white on orange (256-color)
_ERROR_STYLE = "97;41"          # white on red
_SUCCESS_STYLE = "97;42"        # white on green


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
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

    args = parser.parse_args(argv)

    # Enable ANSI escape sequences on the legacy Windows console.
    os.system("")

    # Opt-in logging, activated by a logging.json file in the
    # working directory.
    configure_logging()

    display_program_banner()

    if not args.simple:
        parser.error("Only --simple mode is currently supported.")

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
            )

            print(
                f"  Resolved collision from {tilesets_json_path.name}"
            )
        else:
            print(
                f"  {_paint('Tilesets.json not found: generated tiles will have no collision.', _WARNING_STYLE, sys.stderr)}",
                file=sys.stderr,
            )

            converter = SimpleConverter()

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