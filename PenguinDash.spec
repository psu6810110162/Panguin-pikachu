# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path(SPEC).resolve().parent

datas = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "balance"), "balance"),
    (str(project_root / "schemas"), "schemas"),
    (str(project_root / "style.kv"), "."),
    (str(project_root / "resource_manifest.json"), "."),
    (str(project_root / "build_info.json"), "."),
]

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "server",
        "flask",
        "flask_socketio",
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "docker",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PenguinDash",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PenguinDash",
)
