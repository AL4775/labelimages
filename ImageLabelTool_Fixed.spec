# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['image_label_tool.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['multiprocessing', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'cv2', 'numpy', 'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk'],
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
    a.binaries,
    a.datas,
    [],
    name='ImageLabelTool_Fixed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
