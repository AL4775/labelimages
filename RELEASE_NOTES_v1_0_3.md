# Release Notes - Image Label Tool v1.0.3

## Version 1.0.3 - October 6, 2025

### New Features
- **Smart Navigation Buttons**: Previous and Next buttons are now intelligently disabled when not applicable
  - Previous button disabled when at the first image
  - Next button disabled when at the last image
  - Next Unclassified button disabled when no unclassified images remain
  
- **Warning Message System**: Added warning message in Analysis tab
  - Displays red warning when unclassified images remain
  - Message: "⚠️ Warning: still remaining images to classify. The statistics may be inaccurate."
  - Larger, bold font for better visibility
  - Automatically updates when classification status changes

### Improvements
- Enhanced user experience with better visual feedback
- Improved navigation logic based on current filter state
- More accurate statistical reporting awareness

### Technical Details
- Standalone executable: `ImageLabelTool_v1.0.3.exe` (70MB)
- No Python installation required
- All dependencies included
- Compatible with Windows 11

### Files Included
- `ImageLabelTool_v1.0.3.exe` - Standalone executable
- `run_ImageLabelTool_v1.0.3.bat` - Launch script
- `image_label_tool.py` - Source code (v1.0.3)

### Previous Versions
- v1.0.2: Infinite loop fixes and performance improvements
- v1.0.1: Initial stable release
- v1.0.0: Beta release

### Usage
1. Run the executable directly or use the provided batch file
2. No additional installation required
3. All features work identically to the Python version