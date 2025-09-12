# Development Setup

## Prerequisites
- Python 3.7 or higher
- pip (Python package installer)
- Git

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/image-label-tool.git
cd image-label-tool
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux  
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python image_label_tool.py
```

## Building Executable

### Windows
```bash
# Install PyInstaller (if not already installed)
pip install pyinstaller

# Create spec file
pyi-makespec --onefile --windowed --name "ImageLabelTool" image_label_tool.py

# Build executable
python -m PyInstaller ImageLabelTool.spec
```

The executable will be created in `dist/ImageLabelTool.exe`

### macOS
```bash
pyinstaller --onefile --windowed --name "ImageLabelTool" image_label_tool.py
```

### Linux
```bash
pyinstaller --onefile --name "ImageLabelTool" image_label_tool.py
```

## Development Environment

### Recommended IDE Settings
- **VS Code**: Install Python extension
- **PyCharm**: Configure Python interpreter to use virtual environment
- **Any Editor**: Ensure Python path points to virtual environment

### Code Style
- Follow PEP 8 guidelines
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and small

### Testing
Currently no automated tests. Manual testing involves:
1. Creating test image folders with proper naming
2. Testing all labeling scenarios  
3. Verifying CSV output
4. Testing filter functionality
5. Checking parcel grouping logic

## Project Structure
```
image-label-tool/
├── image_label_tool.py      # Main application
├── requirements.txt         # Dependencies
├── README.md               # Main documentation
├── LICENSE                 # MIT license
├── .gitignore             # Git ignore rules
├── run_tool.bat           # Windows launcher
├── docs/                  # Documentation
│   ├── FEATURES.md        # Feature documentation
│   └── SETUP.md          # This file
├── examples/              # Example files
│   └── README.md         # Naming convention examples
└── dist/                 # Built executable (git ignored)
    └── ImageLabelTool.exe
```

## Common Issues

### Import Errors
- Ensure virtual environment is activated
- Verify all dependencies are installed: `pip list`
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

### PyInstaller Issues
- Use full path to Python executable
- Clear build cache: `pyinstaller --clean ImageLabelTool.spec`
- Check for missing modules in warnings

### UI Issues
- Verify tkinter is available: `python -c "import tkinter"`
- On Linux, install tkinter: `sudo apt-get install python3-tk`
- Check Pillow installation: `python -c "from PIL import Image"`

## Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test thoroughly
3. Update documentation if needed
4. Commit with descriptive message
5. Push and create pull request

### Adding Features
- Keep UI simple and intuitive
- Maintain backward compatibility for CSV format
- Add appropriate error handling
- Update documentation

### Bug Fixes
- Reproduce the issue first
- Write minimal fix
- Test edge cases
- Document the fix