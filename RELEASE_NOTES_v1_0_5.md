# Release Notes - Image Label Tool v1.0.5

## Version 1.0.5 - October 13, 2025

### New Features

#### 📊 Parcel Statistics Pie Chart
- **Interactive Pie Chart**: New "📊 Show Parcel Pie Chart" button in Analysis tab
- **Modal Dialog**: Clean, centered dialog with professional pie chart visualization
- **Accurate Data**: Uses the same calculation logic as Net Stats for consistency
- **Smart Categories**:
  - **Parcels with No Code** (Orange) - Parcels where all images are "no code"
  - **Parcels with Read Failure** (Red) - Parcels where all images are "read failure"
  - **Parcels with Successful Reads** (Green) - Parcels with readable barcodes
- **Automatic Percentages**: Real-time percentage calculation and display

#### 🔧 Improved Auto-Detection Logic
- **Correct Range Calculation**: Now uses `max_id - min_id + 1` instead of just `max_id`
- **Accurate Parcel Counts**: Handles cases where parcel IDs don't start from 1
- **Debug Information**: Console messages show detected ID range for verification
- **Better Statistics**: More precise Net Stats calculations based on actual parcel range

#### 📈 Matplotlib Integration
- **Full Chart Support**: Matplotlib and Seaborn fully enabled and integrated
- **Error Handling**: Graceful degradation when matplotlib is not available
- **Professional Charts**: High-quality pie charts with proper colors and formatting
- **Tkinter Integration**: Seamless embedding of charts in dialog windows

### Improvements
- **Enhanced User Experience**: Visual feedback through interactive charts
- **Data Accuracy**: Consistent calculations across all statistical displays
- **Better Error Messages**: Clear warnings when data is insufficient for charts
- **Performance**: Optimized chart rendering and data processing

### Technical Details
- **Standalone Executable**: `ImageLabelTool_v1.0.5.exe` (90.4 MB)
- **Dependencies Included**: Matplotlib, Seaborn, and all required libraries
- **Platform Compatibility**: Windows 11 optimized
- **Python Version**: Built with Python 3.12.10

### Files Included
- `ImageLabelTool_v1.0.5.exe` - Main standalone executable
- `run_ImageLabelTool_v1.0.5.bat` - Enhanced launch script
- `image_label_tool.py` - Source code (v1.0.5)

### Usage Instructions

#### Using the Pie Chart Feature:
1. Load a folder with images
2. Enter the total number of parcels (auto-detected)
3. Classify some images (optional for testing)
4. Go to Analysis tab
5. Click "📊 Show Parcel Pie Chart"
6. View statistics in an interactive pie chart

#### Auto-Detection:
- Automatically calculates correct parcel count based on filename ID range
- Displays debug information in console for verification
- Updates Net Stats with accurate calculations

### Version History
- **v1.0.5**: Pie chart visualization + improved auto-detection
- **v1.0.4**: Enhanced visual feedback + auto fit-to-window
- **v1.0.3**: Smart navigation buttons + warning message system  
- **v1.0.2**: Infinite loop fixes and performance improvements
- **v1.0.1**: Initial stable release
- **v1.0.0**: Beta release

### Compatibility
- Maintains full backward compatibility with existing CSV files
- No data migration required
- All existing features preserved and enhanced

### Developer Notes
- Added `calculate_parcel_stats_for_chart()` method
- Enhanced `auto_detect_total_groups()` with min/max range logic
- Integrated matplotlib with proper error handling
- Reactivated chart functionality with improved stability