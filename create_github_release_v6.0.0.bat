@echo off
echo ========================================
echo Creating GitHub Release v6.0.0
echo ========================================
echo.
echo Manual Steps to Complete Release:
echo.
echo 1. Go to: https://github.com/almtlsandbox/labelimages/releases/new
echo.
echo 2. Use these settings:
echo    - Tag: v6.0.0 (should be auto-selected)
echo    - Title: "Image Label Tool v6.0.0 - Lightning-Fast Keyboard Shortcuts"
echo.
echo 3. Copy release notes from: release_notes_v6.0.0.md
echo.
echo 4. Upload executable: image_label_tool.exe
echo.
echo 5. Mark as latest release
echo.
echo 6. Click "Publish release"
echo.
echo ========================================
echo Files ready for release:
echo ========================================
dir image_label_tool.exe
echo.
echo Release notes file: release_notes_v6.0.0.md
echo.
pause