# Release Notes - Image Label Tool v1.0.4

## Version 1.0.4 - October 7, 2025

### New Features

#### Enhanced Visual Feedback
- **Smart Button Colors**: Navigation buttons now provide clear visual feedback
  - **Disabled state**: Gray background (`#CCCCCC`) with dark gray text (`#666666`)
  - **Enabled state**: Original colors restored (blue for Prev/Next, orange for Next Unclass)
  - **Real-time updates**: Button states change immediately based on navigation context

#### Automatic Image Fitting
- **Auto Fit-to-Window**: Images automatically fit to display frame after classification
  - Applies to both keyboard shortcuts (Q, W, E, R, T, Y) and radio button selections
  - Ensures consistent viewing experience without manual resizing
  - Maintains user's ability to manually switch to 1:1 scale when needed

### Improvements
- **Better User Experience**: Enhanced visual clarity for navigation state
- **Streamlined Workflow**: Reduced need for manual image scaling adjustments
- **Consistent Behavior**: Unified display logic across all classification methods

### Technical Details
- **Standalone Executable**: `ImageLabelTool_v1.0.4.exe` (70.3 MB)
- **No Dependencies**: Complete standalone application
- **Platform**: Windows 11 compatible
- **Python Version**: Built with Python 3.12.10

### Files Included
- `ImageLabelTool_v1.0.4.exe` - Main standalone executable
- `run_ImageLabelTool_v1.0.4.bat` - Enhanced launch script with feature summary
- `image_label_tool.py` - Source code (v1.0.4)

### Upgrade Path
This version maintains full compatibility with existing CSV files and workflows. No data migration required.

### Version History
- **v1.0.4**: Smart button colors + auto fit-to-window
- **v1.0.3**: Smart navigation buttons + warning message system  
- **v1.0.2**: Infinite loop fixes and performance improvements
- **v1.0.1**: Initial stable release
- **v1.0.0**: Beta release

### Usage Instructions
1. Run `ImageLabelTool_v1.0.4.exe` directly or use the batch launcher
2. No installation required - fully portable application
3. All new features are enabled by default and work automatically

### Developer Notes
- Modified `update_navigation_buttons()` method for visual feedback
- Enhanced `set_label()` and `set_label_radio()` methods for auto-fitting
- Maintained backward compatibility with all existing features