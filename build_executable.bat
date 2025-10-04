@echo off
REM ========================================================
REM Script de construction d'exécutable standalone
REM Image Label Tool - Zebra Technologies
REM ========================================================

echo.
echo ========================================================
echo  Construction de l'executable standalone
echo  Image Label Tool v6.0.0
echo ========================================================
echo.

REM Vérifier si l'environnement virtuel existe
if not exist ".venv\Scripts\activate.bat" (
    echo ERREUR: Environnement virtuel .venv non trouve
    echo Veuillez d'abord executer setup.bat pour creer l'environnement
    pause
    exit /b 1
)

echo [1/5] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat
echo Environnement virtuel active... OK
echo.

REM Vérifier si PyInstaller est installé, sinon l'installer
echo [2/5] Verification des dependances...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installation de PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERREUR: Impossible d'installer PyInstaller
        pause
        exit /b 1
    )
)
echo Dependances... OK
echo.

REM Nettoyer les anciens builds
echo [3/5] Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist ImageLabelTool.exe del ImageLabelTool.exe
echo Nettoyage... OK
echo.

REM Construire l'exécutable avec PyInstaller
echo [4/5] Construction de l'executable (ceci peut prendre plusieurs minutes)...
echo.

python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name=ImageLabelTool ^
  --distpath=. ^
  --workpath=build ^
  --specpath=. ^
  --hidden-import=PIL ^
  --hidden-import=PIL.Image ^
  --hidden-import=PIL.ImageTk ^
  --hidden-import=cv2 ^
  --hidden-import=numpy ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.filedialog ^
  --hidden-import=tkinter.messagebox ^
  --hidden-import=tkinter.ttk ^
  --exclude-module=matplotlib ^
  --exclude-module=seaborn ^
  --exclude-module=pandas ^
  --exclude-module=scipy ^
  --exclude-module=jupyter ^
  --exclude-module=IPython ^
  --exclude-module=plotly ^
  --exclude-module=bokeh ^
  --exclude-module=PyQt5 ^
  --exclude-module=PyQt6 ^
  --exclude-module=PySide2 ^
  --exclude-module=PySide6 ^
  --optimize=2 ^
  --noupx ^
  image_label_tool.py

if errorlevel 1 (
    echo.
    echo ERREUR: Echec de la construction de l'executable
    echo Consultez les messages d'erreur ci-dessus
    pause
    exit /b 1
)

echo.
echo Construction... OK
echo.

REM Vérifier que l'exécutable a été créé
echo [5/5] Verification de l'executable...
if exist ImageLabelTool.exe (
    echo.
    echo ========================================================
    echo  CONSTRUCTION REUSSIE !
    echo ========================================================
    echo.
    echo Executable cree : ImageLabelTool.exe
    echo Taille du fichier:
    for %%f in (ImageLabelTool.exe) do echo   %%~zf bytes (%%~zf octets)
    echo.
    echo L'executable est standalone et ne necessite pas
    echo l'installation de Python ou de dependances.
    echo.
    echo Vous pouvez maintenant copier ImageLabelTool.exe
    echo sur n'importe quel ordinateur Windows.
    echo.
) else (
    echo ERREUR: L'executable n'a pas ete cree
    pause
    exit /b 1
)

REM Nettoyer les fichiers temporaires
echo Nettoyage des fichiers temporaires...
if exist build rmdir /s /q build
if exist ImageLabelTool.spec del ImageLabelTool.spec

echo.
echo ========================================================
echo  Appuyez sur une touche pour fermer cette fenetre
echo ========================================================
pause >nul