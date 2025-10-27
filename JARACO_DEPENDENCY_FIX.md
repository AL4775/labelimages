# Jaraco Dependency Fix for PyInstaller

## Problem
When distributing the Aurora FIS Analytics executable to other machines, users encountered:
```
ModuleNotFoundError: No module named 'jaraco.text'
```

## Root Cause
- Python 3.9 setuptools (v58.1.0) doesn't include jaraco modules in its vendor directory
- Python 3.12+ setuptools includes jaraco modules in setuptools._vendor.jaraco
- PyInstaller relies on pkg_resources which depends on jaraco modules
- Different Python versions have different availability of these modules

## Solution
1. **Install explicit jaraco dependencies** to ensure they're available:
   ```
   pip install jaraco.text jaraco.functools jaraco.context jaraco.collections
   ```

2. **Updated requirements.txt** to include:
   ```
   jaraco.text>=3.0.0
   jaraco.functools>=3.0.0
   jaraco.context>=4.0.0
   jaraco.collections>=3.0.0
   ```

3. **Updated PyInstaller spec** to properly collect jaraco modules:
   ```python
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
   ```

## Verification
- Built executable is now ~255MB and includes all jaraco dependencies
- No more "ModuleNotFoundError: No module named 'jaraco.text'" on target machines
- Executable works on any Windows machine without requiring Python installation

## Build Information
- **Development Environment**: Python 3.9.10, PyInstaller 6.16.0
- **Target Environment**: Any Windows machine (no Python required)
- **Executable Size**: 255MB (includes all dependencies)
- **Dependencies**: All jaraco modules properly bundled

This fix ensures cross-platform compatibility for the Aurora FIS Analytics standalone executable.