# -*- mode: python ; coding: utf-8 -*-
# Simplified PyInstaller spec file for Aurora FIS Analytics
# This creates a standalone executable with core dependencies

block_cipher = None

a = Analysis(
    ['image_label_tool.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include documentation files if they exist
        ('README.md', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        # Core GUI components
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog', 
        'tkinter.messagebox',
        
        # Image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'cv2',
        'numpy',
        
        # Data handling
        'pandas',
        'csv',
        
        # Plotting (matplotlib components your app actually uses)
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        
        # System modules
        'os',
        'sys', 
        'threading',
        'time',
        'datetime',
        'logging',
        'glob',
        'pathlib',
        
        # Package resource dependencies
        'pkg_resources',
        'jaraco.text',
        'jaraco',
        'jaraco.functools',
        'jaraco.context',
        'more_itertools',
        'importlib_metadata',
        'zipp',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy modules not needed
        'PyQt5',
        'PyQt6',
        'PySide2', 
        'PySide6',
        'wx',
        'IPython',
        'jupyter',
        'notebook',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AuroraFISAnalytics',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)