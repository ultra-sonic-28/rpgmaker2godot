# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller recipe for the standalone rpgmaker2godot executable.

Build from the repository root with:

    python -m PyInstaller --clean --noconfirm rpgmaker2godot.spec

The single-file binary lands in ``dist\\rpgmaker2godot.exe`` with
every runtime dependency (Pillow, rich) bundled inside.
"""

import tomllib
from datetime import date
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

datas = copy_metadata("rpgmaker2godot")

# ---------------------------------------------------------------------------
# Windows version metadata, sourced from pyproject.toml so the numbers can
# never drift from the package definition. scripts/build_exe.ps1 bumps the
# `build` entry BEFORE invoking PyInstaller, hence the freshly stamped value
# is the one read here.
# ---------------------------------------------------------------------------
_project = tomllib.loads(
    # PyInstaller exposes SPECPATH (the spec file's directory) instead
    # of __file__ when executing the recipe.
    (Path(SPECPATH) / "pyproject.toml").read_text(
        encoding="utf-8",
    ),
)["project"]

VERSION = _project["version"]
BUILD_NUMBER = int(_project["build"])

_file_version_tuple = (
    tuple(int(part) for part in VERSION.split(".")) + (BUILD_NUMBER,)
)
while len(_file_version_tuple) < 4:
    _file_version_tuple += (0,)

COPYRIGHT = f"© {date.today().year} ultra-sonic-28"

vs_version = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=_file_version_tuple[:4],
        prodvers=_file_version_tuple[:4],
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        VarFileInfo(
            # 1036 = French (France), 1200 = Unicode.
            [VarStruct("Translation", [1036, 1200])],
        ),
        StringFileInfo(
            [
                StringTable(
                    # Key = language id (040C) + charset id (04B0)
                    # hex-encoded: French (1036) + Unicode (1200).
                    "040C04B0",
                    [
                        StringStruct(
                            "FileDescription",
                            "Convert RPG Maker MV/MZ tilesets "
                            "to Godot resources.",
                        ),
                        StringStruct(
                            "FileVersion",
                            f"{VERSION} build {BUILD_NUMBER}",
                        ),
                        StringStruct("InternalName", "rpgmaker2godot"),
                        StringStruct("LegalCopyright", COPYRIGHT),
                        StringStruct(
                            "OriginalFilename",
                            "rpgmaker2godot.exe",
                        ),
                        StringStruct("ProductName", "rpgmaker2godot"),
                        StringStruct(
                            "ProductVersion",
                            f"{VERSION} build {BUILD_NUMBER}",
                        ),
                    ],
                ),
            ],
        ),
    ],
)

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "pydoc_data",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="rpgmaker2godot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=vs_version,
    icon="assets/icon/rpgmaker2godot.ico",
)