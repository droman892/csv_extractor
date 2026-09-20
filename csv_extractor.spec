# PyInstaller spec for CSV Extractor.
#
# Build:   pyinstaller csv_extractor.spec
# Output:  dist/CSV Extractor.exe (a single file)
#
# It is a one-file build for easy distribution (one .exe to hand
# someone), at the cost of a slower start-up: each launch unpacks the
# app into a temp folder before it runs. See docs/architecture.md if
# start-up time ever needs to be a onedir build instead.

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    # The upload screen's "try it with a sample file" link reads this
    # file at runtime (src/services/demo_file_service.py); it is not
    # imported code, so PyInstaller would not pick it up on its own.
    datas=[('data/demo_data.csv', 'data')],
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
    name='CSV Extractor',
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
