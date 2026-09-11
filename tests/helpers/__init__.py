"""Shared helpers used across the test-suite."""

from pathlib import Path

# The startup banner reads the program version from the installed
# package metadata, which mirrors ``[project].version`` in
# pyproject.toml. Tests must therefore never pin a concrete number
# (e.g. "rpgmaker2godot v0.1.0"): a version bump would otherwise break
# the suite for no reason. This pattern only matches the
# "name v<version-number>" shape of the banner line.
PROGRAM_BANNER_VERSION = r"rpgmaker2godot v\d+(\.\d+)*"


def write_converter_config(
    input_directory,
    output_directory,
):
    """Drop a converter configuration in the (sandboxed) working directory.

    The converter paths are no longer command-line arguments: tests
    must publish them through ``rpgmaker2godot.yaml`` exactly like a
    real run does. Returns the written configuration path.
    """

    import yaml

    config_path = Path.cwd() / "rpgmaker2godot.yaml"

    config_path.write_text(
        yaml.safe_dump(
            {
                "converter": {
                    "path": {
                        "input": str(input_directory),
                        "output": str(output_directory),
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    return config_path
