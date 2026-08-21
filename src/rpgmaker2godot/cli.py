import argparse
import sys
from collections import defaultdict
from pathlib import Path

from .analysis.detector import TilesetDetector
from .conversion.converter import SimpleConverter
from .godot.export.simple import SimpleExporter


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

        print(f"Input: {result.input_directory}")
        print(f"Tile size: {result.tile_width}x{result.tile_height}")
        print()
        print("Sheets:")

        groups: dict[str, list] = defaultdict(list)

        for sheet in result.sheets:
            groups[sheet.prefix].append(sheet)

        sheet_order = {
            "A5": 0,
            "B": 1,
            "C": 2,
            "D": 3,
            "E": 4,
        }

        for prefix, sheets in sorted(groups.items()):
            print()
            print(f"  {prefix or '(no prefix)'}")

            for sheet in sorted(
                sheets,
                key=lambda sheet: sheet_order[sheet.sheet_type.value],
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

        converter = SimpleConverter()
        conversion = converter.convert(result)

        exporter = SimpleExporter()
        generated = exporter.export(
            conversion,
            args.output,
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
    ) as error:
        print(
            f"Error: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())