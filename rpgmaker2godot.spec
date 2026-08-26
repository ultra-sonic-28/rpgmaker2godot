# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller recipe for the standalone rpgmaker2godot executable.

Build from the repository root with:

    python -m PyInstaller --clean --noconfirm rpgmaker2godot.spec

The single-file binary lands in ``dist\\rpgmaker2godot.exe`` with
every runtime dependency (Pillow, rich) bundled inside.
"""

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata("rpgmaker2godot")

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
    icon="assets/icon/rpgmaker2godot.ico",
)