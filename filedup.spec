# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('filedup', 'filedup'), ('gui_dupl', 'gui_dupl'), ('reg_handlers.json', '.')],
    hiddenimports=['filedup', 'gui_dupl', 'filedup.file_duplicate_finder', 'filedup.global_vars', 'filedup.prograss', 'filedup.rw_video', 'filedup.rw_docx_wps', 'filedup.rw_img', 'filedup.rw_interface', 'filedup.rw_reg_handlers', 'gui_dupl.handle_dupl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='filedup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='filedup',
)
