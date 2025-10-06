@echo off
echo ========================================================
echo  Quick Build - Fixed Executable
echo ========================================================

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Nettoyer
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del ImageLabelTool_Fixed.spec

echo Building fixed executable (this may take a few minutes)...

REM Construction simple avec protection multiprocessing
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name=ImageLabelTool_Fixed ^
  --hidden-import=multiprocessing ^
  --hidden-import=PIL ^
  --hidden-import=PIL.Image ^
  --hidden-import=PIL.ImageTk ^
  --hidden-import=cv2 ^
  --hidden-import=numpy ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.filedialog ^
  --hidden-import=tkinter.messagebox ^
  --hidden-import=tkinter.ttk ^
  image_label_tool.py

if exist dist\ImageLabelTool_Fixed.exe (
    copy dist\ImageLabelTool_Fixed.exe .
    echo.
    echo ========================================================
    echo SUCCESS! Fixed executable created: ImageLabelTool_Fixed.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo BUILD FAILED
    echo ========================================================
)

pause