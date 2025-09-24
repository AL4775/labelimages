@echo off
REM ========================================================
REM Test de l'executable standalone
REM Verifie que l'executable fonctionne correctement
REM ========================================================

echo.
echo =======================================
echo  TEST DE L'EXECUTABLE STANDALONE
echo =======================================
echo.

REM Verifier que l'executable existe
if not exist ImageLabelTool.exe (
    echo [ERROR] ImageLabelTool.exe n'existe pas
    echo Vous devez d'abord construire l'executable avec:
    echo    build_venv.bat
    echo.
    pause
    exit /b 1
)

echo [INFO] Executable trouve: ImageLabelTool.exe

REM Afficher les informations du fichier
for %%f in (ImageLabelTool.exe) do (
    set /a size_mb=%%~zf/1024/1024
    echo [INFO] Taille: !size_mb! MB (%%~zf octets)
    echo [INFO] Date: %%~tf
)
echo.

echo [INFO] Lancement de l'executable...
echo        (Une fenetre devrait s'ouvrir)
echo.

REM Lancer l'executable
start "" ImageLabelTool.exe

echo [INFO] Executable lance!
echo.
echo Si l'application s'ouvre correctement,
echo l'executable standalone fonctionne.
echo.
echo Testez les fonctionnalites principales:
echo - Selection de dossier d'images
echo - Navigation entre images  
echo - Classification avec radio buttons
echo - Zoom et affichage
echo - Generation de CSV de statistiques
echo.
echo =======================================
echo  TEST TERMINE
echo =======================================
echo.

pause