import argparse
from pathlib import Path
from collections import defaultdict

from .analysis.detector import TilesetDetector


def main() -> None:
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

    args = parser.parse_args()

    if not args.simple:
        parser.error("Only --simple mode is currently supported.")

    detector = TilesetDetector()
    result = detector.analyze(args.input)

    print(f"Input: {result.input_directory}")
    print(f"Tile size: {result.tile_width}x{result.tile_height}")
    print()
    print("Sheets:")

    groups: dict[str, list] = defaultdict(list)

    for sheet in result.sheets:
        groups[sheet.prefix].append(sheet)

    for prefix, sheets in groups.items():
        print()
        print(f"  {prefix or '(no prefix)'}")

        for sheet in sheets:
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


if __name__ == "__main__":
    main()