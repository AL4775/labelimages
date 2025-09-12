# Image Label Tool

A professional image labeling tool for efficient review and categorization of images. Built with Python and Tkinter, featuring a modern UI and comprehensive statistics tracking.

![Image Label Tool](docs/screenshot.png)

## Features

✅ **Smart Image Loading** - Automatically filters images with `_number` naming pattern  
✅ **Fast Labeling** - Color-coded radio buttons for quick classification  
✅ **Parcel Grouping** - Groups images by number suffix with intelligent labeling rules  
✅ **CSV Export** - Timestamped CSV files with image and parcel information  
✅ **Progress Tracking** - Real-time statistics with percentage calculations  
✅ **Filter System** - Focus on specific label categories  
✅ **Modern UI** - Professional design with intuitive color coding  
✅ **Standalone Executable** - No Python installation required for end users  

## Label Categories

- **no label** - Default state for unlabeled images
- **no read** - Images that haven't been read/processed yet  
- **unreadable** - Images that are unreadable or corrupted

## Parcel Logic

Images with the same number after the underscore (`_`) belong to the same parcel:
- `document_1.jpg`, `page_1.png` → Parcel "1"
- `scan_25.jpg`, `image_25.jpeg` → Parcel "25"

Parcel labeling rules:
- If **all** images in a parcel are "no label" → Parcel is **"no label"**
- If **at least one** image is "no read" → Parcel is **"no read"**  
- If mix of "no label" and "unreadable" → Parcel is **"unreadable"**

## Installation

### Option 1: Use Pre-built Executable (Recommended)
1. Download `ImageLabelTool.exe` from the releases
2. Run the executable directly - no installation needed!

### Option 2: Run from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/image-label-tool.git
   cd image-label-tool
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python image_label_tool.py
   ```

## Usage

1. **Select Folder** - Click "Select Folder" and choose a directory containing images
2. **Set Total Parcels** (optional) - Enter expected total number of parcels for progress tracking
3. **Filter Images** - Use the dropdown to focus on specific label categories
4. **Label Images** - Click the color-coded radio buttons to assign labels
5. **Navigate** - Use "Prev" and "Next" buttons to move between images
6. **Track Progress** - Monitor statistics in real-time

### Expected Image Naming

Images must follow the pattern: `basename_number.extension`

**Examples:**
- ✅ `document_1.jpg`
- ✅ `page_025.png` 
- ✅ `scan_123.jpeg`
- ❌ `document.jpg` (no number)
- ❌ `page_a.png` (not a number)

## Output

The tool creates timestamped CSV files in the selected folder:
- Filename: `revision_YYYYMMDD_HHMMSS.csv`
- Contains: image path, image label, parcel number, parcel label

**Example CSV:**
```csv
image_path,image_label,parcel_number,parcel_label
/path/to/doc_1.jpg,no label,1,no label
/path/to/page_1.png,no label,1,no label
/path/to/doc_2.jpg,no read,2,no read
/path/to/page_2.png,unreadable,2,no read
```

## Building Executable

To create your own executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Create the executable:
   ```bash
   pyinstaller --onefile --windowed --name "ImageLabelTool" image_label_tool.py
   ```

3. Find the executable in the `dist/` folder

## Development

### Project Structure
```
image-label-tool/
├── image_label_tool.py      # Main application
├── requirements.txt         # Python dependencies
├── README.md               # Documentation
├── .gitignore             # Git ignore rules
├── docs/                  # Documentation assets
│   └── screenshot.png     # Application screenshot
├── examples/              # Example images
│   ├── document_1.jpg
│   ├── document_2.jpg
│   └── document_3.jpg
└── dist/                  # Built executable (excluded from git)
    └── ImageLabelTool.exe
```

### Requirements
- Python 3.7+
- tkinter (usually included with Python)
- Pillow (PIL) for image handling
- PyInstaller (for building executable)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python and Tkinter
- Uses Pillow library for image processing
- Created for efficient image review workflows

---

**Need help?** Open an issue or check the [documentation](docs/).