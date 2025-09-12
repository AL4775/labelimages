# Features Documentation

## User Interface

### Main Components

1. **Select Folder Button** - Green button to choose image directory
2. **Total Parcels Input** - Manual entry for expected parcel count
3. **Filter Dropdown** - Focus on specific label categories
4. **Image Display** - Shows current image with border
5. **Navigation Buttons** - Blue Prev/Next buttons
6. **Label Radio Buttons** - Color-coded for quick selection
7. **Statistics Display** - Real-time progress tracking

### Color Coding

- **no label**: Orange (`#FFB74D`) - Default state
- **no read**: Pink (`#F06292`) - Not yet processed  
- **unreadable**: Purple (`#BA68C8`) - Cannot be read

## Workflow

### Basic Labeling
1. Select folder containing images
2. Optionally set total expected parcels
3. Use radio buttons to label each image
4. Navigate with Prev/Next buttons
5. CSV automatically saves changes

### Advanced Features
- **Filter by label** - Show only images with specific labels
- **Parcel statistics** - Track progress at group level
- **Progress tracking** - Percentage completion against total
- **Auto-save** - Changes saved immediately to CSV

## File Management

### Input Requirements
- Images must end with `_number.extension`
- Supported formats: PNG, JPG, JPEG, BMP, GIF
- Files grouped by number after underscore

### Output Format
- CSV files named `revision_YYYYMMDD_HHMMSS.csv`
- Contains: image_path, image_label, parcel_number, parcel_label
- Saved in the same folder as images
- Automatically loads most recent revision on folder selection

## Statistics

### Individual Images
Shows count of images in each label category.

### Parcel Groups  
Shows count of parcels in each category based on grouping rules.

### Progress vs Total
When total parcels is set:
- Shows percentage for each category
- Calculates "read" as complement of no_read + unreadable
- Helps track overall completion

## Keyboard Shortcuts
Currently navigation is mouse-based. Future versions may include:
- Arrow keys for navigation
- Number keys for quick labeling
- Keyboard shortcuts for common actions