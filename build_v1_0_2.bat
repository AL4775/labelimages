@echo off
echo ========================================================
echo  Build ImageLabelTool v1.0.2
echo ========================================================

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Nettoyer
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del "ImageLabelTool_1_0_2.spec"

echo Building ImageLabelTool v1.0.2 (this may take a few minutes)...

REM Construction avec le nom de version
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name=ImageLabelTool_1_0_2 ^
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

if exist dist\ImageLabelTool_1_0_2.exe (
    copy dist\ImageLabelTool_1_0_2.exe .
    echo.
    echo ========================================================
    echo SUCCESS! ImageLabelTool v1.0.2 created: ImageLabelTool_1_0_2.exe
    echo ========================================================
    
    REM Afficher les détails du fichier
    for %%f in (ImageLabelTool_1_0_2.exe) do (
        echo File size: %%~zf bytes
        echo Created: %%~tf
    )
) else (
    echo.
    echo ========================================================
    echo BUILD FAILED - Check error messages above
    echo ========================================================
)

pause