import argparse
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

from .analysis.detector import TilesetDetector
from .conversion.converter import SimpleConverter
from .godot.export.simple import SimpleExporter
from .tileset.reader import TilesetsJsonReader
from .tileset.resolver import TilePropertiesResolver

TOTAL_STEPS = 4


def _print_step(
    step: int,
    label: str,
) -> None:
    """Print a numbered pipeline step heading."""

    print()
    print(f"[{step}/{TOTAL_STEPS}] {label}")


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
                print(f"  - {warning}")

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
                "  Tilesets.json not found: "
                "generated tiles will have no collision.",
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

            print(
                f"  {tileset.name}: "
                f"{tile_count} tiles "
                f"from {len(tileset.sheets)} sheets"
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
        print("Generated:")

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
            f"Error: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())