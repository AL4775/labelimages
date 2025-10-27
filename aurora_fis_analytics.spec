# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Aurora FIS Analytics INTERNAL tool
# This creates a standalone executable with all dependencies included

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Ensure setuptools is available for vendored jaraco modules
try:
    import setuptools
    import pkg_resources
except ImportError:
    pass

# Define the main script
main_script = 'image_label_tool.py'

# Collect data files for matplotlib (fonts, data files, etc.)
matplotlib_datas = collect_data_files('matplotlib')

# Collect data files for seaborn (styling files)
seaborn_datas = collect_data_files('seaborn')

# Additional data files for OpenCV
opencv_datas = collect_data_files('cv2')

# Collect all submodules for critical packages
matplotlib_hiddenimports = collect_submodules('matplotlib')
seaborn_hiddenimports = collect_submodules('seaborn')
cv2_hiddenimports = collect_submodules('cv2')

# Collect jaraco submodules (now that we have them installed)
try:
    jaraco_hiddenimports = collect_submodules('jaraco')
    # Filter out CLI tools with hyphens in names
    jaraco_hiddenimports = [mod for mod in jaraco_hiddenimports if '-' not in mod.split('.')[-1]]
except Exception as e:
    print(f"Warning: Could not collect jaraco modules: {e}")
    jaraco_hiddenimports = [
        'jaraco.text',
        'jaraco.functools', 
        'jaraco.context',
        'jaraco.collections',
    ]

block_cipher = None

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=[
        # Include matplotlib data files
        *matplotlib_datas,
        # Include seaborn data files  
        *seaborn_datas,
        # Include OpenCV data files
        *opencv_datas,
        # Include any additional data files your app might need
        ('*.md', '.'),  # Include documentation files
        ('*.txt', '.'),  # Include text files like requirements.txt
    ],
    hiddenimports=[
        # Core GUI and image processing
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        
        # Computer vision
        'cv2',
        'numpy',
        
        # Data processing
        'pandas',
        'csv',
        
        # Plotting and visualization
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.style',
        'seaborn',
        
        # Additional hidden imports discovered by collect_submodules
        *matplotlib_hiddenimports,
        *seaborn_hiddenimports,
        *cv2_hiddenimports,
        *jaraco_hiddenimports,
        
        # System and file operations
        'os',
        'sys',
        'threading',
        'time',
        'datetime',
        'logging',
        'glob',
        'pathlib',
        'subprocess',
        
        # Additional imports that might be dynamically loaded
        'pkg_resources',
        'pkg_resources.py2_warn',
        
        # jaraco dependencies (now properly installed)
        'jaraco',
        'jaraco.text',
        'jaraco.functools', 
        'jaraco.context',
        'jaraco.collections',
        
        # setuptools and its vendored packages
        'setuptools',
        'setuptools._vendor',
        'setuptools._vendor.packaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'PyQt5',
        'PyQt6', 
        'PySide2',
        'PySide6',
        'wx',
        'gtk',
        'IPython',
        'jupyter',
        'notebook',
        'tornado',
        'sphinx',
        'pytest',
        # Don't exclude setuptools - it's needed for jaraco modules
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out any problematic or unnecessary files
a.datas = [x for x in a.datas if not x[0].startswith('matplotlib/tests')]
a.datas = [x for x in a.datas if not x[0].startswith('seaborn/tests')]

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
    upx=True,  # Enable UPX compression to reduce file size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have an .ico file
    version_file=None,  # Add version info file here if needed
    uac_admin=False,  # Set to True if admin privileges are required
    uac_uiaccess=False,
)