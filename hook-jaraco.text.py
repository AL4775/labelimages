# PyInstaller hook for jaraco.text
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('jaraco.text')
datas = collect_data_files('jaraco.text')
