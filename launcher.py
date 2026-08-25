"""Frozen-executable entry point for rpgmaker2godot.

PyInstaller analyzes a plain script: targeting the package module
directly would break its relative imports. This launcher only
delegates to the real CLI entry point.
"""

from rpgmaker2godot.cli import main

if __name__ == "__main__":
    raise SystemExit(main())