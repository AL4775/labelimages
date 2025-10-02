# Image Label Tool – Architecture Overview

## Purpose
A standalone, cross-platform desktop tool for rapid image labeling, statistics visualization, and dataset management. Built for ease of use, portability, and extensibility.

---

## High-Level Architecture

### 1. **User Interface (UI) Layer**
- **Framework:** Tkinter (Python standard GUI library)
- **Responsibilities:**
  - Main window, toolbars, dialogs, and all user interactions
  - Image display canvas with zoom/pan/fit controls
  - Label selection (radio buttons, keyboard shortcuts)
  - Navigation (next/prev, jump to unclassified)
  - Statistics and charts (matplotlib/seaborn embedded in Tkinter)

### 2. **Image Management Layer**
- **Responsibilities:**
  - Loading images from user-selected folders
  - Tracking current image, navigation state, and label assignments
  - Managing filtered views (e.g., unclassified only)
  - Handling new file detection and auto-refresh

### 3. **Labeling & Data Layer**
- **Responsibilities:**
  - Storing label assignments in memory
  - Saving/loading labels to CSV for persistence
  - Assigning parcel indices and tracking labeling progress
  - Exporting filtered datasets and statistics

### 4. **Visualization & Analytics Layer**
- **Libraries:** matplotlib, seaborn, pandas
- **Responsibilities:**
  - Generating histograms, pie charts, and progress overviews
  - Embedding charts directly in the UI
  - Calculating and displaying real-time statistics

### 5. **Build & Distribution**
- **Tools:** PyInstaller, batch scripts
- **Responsibilities:**
  - Building a single-file, standalone Windows executable
  - Bundling all dependencies (no Python install required)
  - Scripts for fast build, full build, and independence testing

---

## Key Files & Directories
- `image_label_tool.py` – Main application logic and UI
- `requirements.txt` – Python dependencies
- `build_venv.bat` / `build_executable.bat` – Build scripts
- `ImageLabelTool.exe` – Standalone executable (output)
- `test_executable_independence.bat` – Test script for standalone validation
- `docs/` – Additional documentation

---

## Extensibility
- Modular class design: add new label types, analytics, or export formats easily
- UI and logic separated for maintainability
- All major features (labeling, navigation, charts, export) are encapsulated in methods

---

## Technology Stack
- **Python 3.12+**
- **Tkinter** (UI)
- **Pillow** (image handling)
- **OpenCV** (image processing)
- **NumPy** (numerical ops)
- **matplotlib/seaborn/pandas** (charts/stats)
- **PyInstaller** (packaging)

---

## Typical Workflow
1. User selects a folder of images
2. Images are loaded and displayed one by one
3. User labels each image (radio, keyboard, or auto-detect)
4. Labels and stats are saved to CSV
5. User can view charts, export filtered sets, or build a standalone EXE

---

## Contact & Contribution
- For questions, see `README.md` or contact the maintainer
- Contributions welcome via pull request
