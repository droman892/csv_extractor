# PyInstaller spec for CSV Extractor.
#
# Build:   pyinstaller csv_extractor.spec
# Output:  dist/CSV-Extractor.exe (a single file)
#
# It is a one-file build for easy distribution (one .exe to hand
# someone), at the cost of a slower start-up: each launch unpacks the
# app into a temp folder before it runs. See docs/architecture.md if
# start-up time ever needs to be a onedir build instead.

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['src/csv_extractor/__main__.py'],
    pathex=['src'],
    binaries=[],
    # Non-code files inside the package (the sample CSV in resources/).
    # PyInstaller only follows imports, so it would not find them on its
    # own; this keeps them at the same place inside the package, where
    # demo_file_service.py looks them up.
    datas=collect_data_files('csv_extractor'),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    # No space, so the release download URL needs no escaping.
    name='CSV-Extractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # No console window: this is a GUI app, and a stray console would
    # also let its window steal focus on every launch.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
