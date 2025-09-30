@echo off
REM ========================================================
REM Construction rapide d'executable standalone
REM Version adaptee pour environnement virtuel Python
REM ========================================================

setlocal enabledelayedexpansion

echo.
echo ====================================
echo  BUILD EXECUTABLE STANDALONE
echo ====================================
echo.

REM Definir le chemin Python de l'environnement virtuel
set PYTHON_PATH="C:/Users/AL4775/OneDrive - Zebra Technologies/Documents/AL DOCUMENTS/RandD/Aurora Focus/DEV/labelimages/.venv/Scripts/python.exe"
set PYINSTALLER_PATH="C:/Users/AL4775/OneDrive - Zebra Technologies/Documents/AL DOCUMENTS/RandD/Aurora Focus/DEV/labelimages/.venv/Scripts/pyinstaller.exe"

REM Nettoyer les anciens builds
if exist ImageLabelTool.exe del ImageLabelTool.exe
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1

echo [INFO] Nettoyage effectue
echo [INFO] Utilisation de l'environnement virtuel Python
echo.

REM Verifier que PyInstaller est disponible
if not exist %PYINSTALLER_PATH% (
    echo [ERROR] PyInstaller non trouve dans l'environnement virtuel
    echo Installation de PyInstaller...
    %PYTHON_PATH% -m pip install pyinstaller
)

REM Construction avec parametres optimises
echo [INFO] Construction en cours...
echo        (Ceci peut prendre 2-5 minutes)
echo.

%PYINSTALLER_PATH% ^
    --onefile ^
    --noconsole ^
    --name=ImageLabelTool ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=matplotlib ^
    --hidden-import=matplotlib.pyplot ^
    --hidden-import=matplotlib.backends.backend_tkagg ^
    --hidden-import=seaborn ^
    --hidden-import=pandas ^
    --exclude-module=scipy ^
    --exclude-module=jupyter ^
    --optimize=2 ^
    image_label_tool.py

REM Copier l'executable du dossier dist vers le repertoire courant
if exist dist\ImageLabelTool.exe (
    copy dist\ImageLabelTool.exe . >nul
    echo.
    echo [SUCCESS] Executable cree: ImageLabelTool.exe
    
    REM Afficher la taille du fichier
    for %%f in (ImageLabelTool.exe) do (
        set /a size_mb=%%~zf/1024/1024
        echo [INFO] Taille: !size_mb! MB (%%~zf octets)
    )
    
    REM Nettoyer les dossiers temporaires
    rmdir /s /q build >nul 2>&1
    rmdir /s /q dist >nul 2>&1
    if exist ImageLabelTool.spec del ImageLabelTool.spec >nul 2>&1
    
    echo.
    echo ====================================
    echo  EXECUTABLE PRET !
    echo ====================================
    echo.
    echo Fichier: ImageLabelTool.exe
    echo.
    echo Cet executable est completement
    echo autonome et ne necessite aucune
    echo installation de Python.
    echo.
    echo Vous pouvez maintenant copier ce fichier
    echo sur n'importe quel ordinateur Windows
    echo et l'executer directement.
    echo.
    
) else (
    echo.
    echo [ERROR] Echec de la construction
    echo Consultez les messages d'erreur ci-dessus
    echo.
)

echo Appuyez sur une touche pour continuer...
pause >nul