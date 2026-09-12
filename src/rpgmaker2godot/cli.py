"""Command-line entry point of rpgmaker2godot.

Only the ``main`` function lives here: it wires the argument parser,
the configuration checks and the conversion pipeline together. Every
other routine (parser classes, rendering helpers and the pipeline
steps of both conversion modes) is defined in :mod:`cli_helper`.
"""

import os

from .cli_helper import (
    _format_usage_error,
    _Parser,
    _run_character_mode,
    _run_tileset_mode,
    _UsageError,
    _warn_ignored_tileset_options,
)
from .utils.config import (
    load_app_config,
    missing_converter_paths,
    read_yaml_document,
    resolve_config_path,
)
from .utils.log import configure_logging
from .utils.messages import (
    display_error,
    display_info,
    display_program_banner,
    display_warning,
)


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(
        prog="rpgmaker2godot",
        description="Convert RPG Maker MV/MZ tilesets to Godot resources.",
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
            "Merge unfolded A1/A2/A3/A4 autotile tiles whose pixel "
            "difference is within N pixels, discarding source-image "
            "noise (default: 0, byte-exact match)."
        ),
    )

    parser.add_argument(
        "--no-terrains",
        action="store_true",
        help=(
            "Skip Godot terrain generation for the unfolded A1/A2/A3/A4 "
            "autotiles (terrains power the automatic connection tool "
            "in the Godot editor)."
        ),
    )

    parser.add_argument(
        "--config",
        metavar="CONFIG",
        default=None,
        help=(
            "Load the configuration from this YAML file instead of the "
            "default rpgmaker2godot.yaml looked up in the working "
            "directory (the .yaml extension is assumed when omitted, "
            "so --config prod loads prod.yaml). Every section of the "
            "file (converter, logger, tileset, character) drives the "
            "run. The converter.path.input and converter.path.output "
            "entries are mandatory."
        ),
    )

    # Enable ANSI escape sequences on the legacy Windows console.
    os.system("")

    display_program_banner()

    try:
        args = parser.parse_args(argv)
    except _UsageError as error:
        display_warning(
            _format_usage_error(parser, error.message),
        )

        return 2

    config_path = resolve_config_path(args.config)

    # Tell the user which configuration file drives this run: the
    # default rpgmaker2godot.yaml looked up in the working directory,
    # or the file explicitly named with --config.
    if args.config is not None:
        display_info(
            f"Configuration file: {config_path} (--config {args.config})",
        )

    else:
        display_info(
            f"Configuration file: {config_path} (default lookup in the "
            f"working directory)",
        )

    # An explicitly named configuration file must exist: silently
    # falling back to the defaults would only hide a typo.
    if args.config is not None and not config_path.is_file():
        display_warning(
            _format_usage_error(
                parser,
                (
                    f"Configuration file '{config_path}' not found "
                    f"(--config {args.config})."
                ),
            ),
        )

        return 2

    # A configuration file that exists but cannot be parsed (invalid
    # YAML syntax, a scalar at the root...) must be reported instead
    # of being silently treated as empty: the user would otherwise see
    # misleading complaints about missing sections.
    _, config_parse_error = read_yaml_document(args.config)

    if config_parse_error is not None:
        display_warning(
            _format_usage_error(
                parser,
                (
                    f"Configuration file '{config_path}' is invalid: "
                    f"{config_parse_error}"
                ),
            ),
        )

        return 2

    # Opt-in logging, activated by the configuration file: the
    # default rpgmaker2godot.yaml in the working directory, or the
    # file named by --config.
    configure_logging(config_path)

    character_mode = args.mode == "CHARACTER"

    if character_mode:
        _warn_ignored_tileset_options(args)

    else:
        if args.tolerance < 0:
            display_warning(
                _format_usage_error(
                    parser,
                    "--tolerance must be >= 0.",
                ),
            )

            return 2

    # The converter.path.input and converter.path.output entries are
    # mandatory: their presence is checked before the detection and
    # analysis pipeline starts. A missing entry is reported through a
    # usage-style warning and nothing is converted.
    missing_paths = missing_converter_paths(args.config)

    if missing_paths:
        missing_list = ", ".join(missing_paths)

        display_warning(
            _format_usage_error(
                parser,
                (
                    f"Missing required configuration entries in "
                    f"'{config_path}': {missing_list} "
                    f"(converter.path section)."
                ),
            ),
        )

        return 2

    app_config = load_app_config(config_path)

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
        display_error(f"Error: {error}")

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
