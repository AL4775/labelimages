@echo off
REM ========================================================
REM Construction rapide d'executable standalone
REM Version simplifiee pour Image Label Tool
REM ========================================================

setlocal enabledelayedexpansion

echo.
echo ====================================
echo  BUILD EXECUTABLE STANDALONE
echo ====================================
echo.

REM Nettoyer les anciens builds
if exist ImageLabelTool.exe del ImageLabelTool.exe
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1

echo [INFO] Nettoyage effectue
echo.

REM Construction avec parametres optimises
echo [INFO] Construction en cours...
echo        (Ceci peut prendre 2-5 minutes)
echo.

pyinstaller --onefile --noconsole --name=ImageLabelTool image_label_tool.py

REM Copier l'executable du dossier dist vers le repertoire courant
if exist dist\ImageLabelTool.exe (
    copy dist\ImageLabelTool.exe . >nul
    echo [SUCCESS] Executable cree: ImageLabelTool.exe
    
    REM Afficher la taille du fichier
    for %%f in (ImageLabelTool.exe) do (
        set /a size_mb=%%~zf/1024/1024
        echo [INFO] Taille: !size_mb! MB
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
    
) else (
    echo [ERROR] Echec de la construction
    echo Verifiez que PyInstaller est installe:
    echo    pip install pyinstaller
    echo.
)

pause