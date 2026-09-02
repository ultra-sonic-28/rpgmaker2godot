"""Shared helpers used across the test-suite."""

# The startup banner reads the program version from the installed
# package metadata, which mirrors ``[project].version`` in
# pyproject.toml. Tests must therefore never pin a concrete number
# (e.g. "rpgmaker2godot v0.1.0"): a version bump would otherwise break
# the suite for no reason. This pattern only matches the
# "name v<version-number>" shape of the banner line.
PROGRAM_BANNER_VERSION = r"rpgmaker2godot v\d+(\.\d+)*"
