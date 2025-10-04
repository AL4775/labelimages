#!/usr/bin/env python3
"""
Launcher script for VS Code to ensure correct environment
"""
import sys
import os
from pathlib import Path

# Ensure we're using the virtual environment
script_dir = Path(__file__).parent
venv_python = script_dir / ".venv" / "Scripts" / "python.exe"

if venv_python.exists() and str(venv_python) not in sys.executable:
    print(f"Switching to virtual environment: {venv_python}")
    os.execv(str(venv_python), [str(venv_python), __file__] + sys.argv[1:])

# Now run the actual application
if __name__ == "__main__":
    # Import and run the main application
    from image_label_tool import ImageLabelTool
    import tkinter as tk
    
    try:
        from PIL import Image, ImageTk
    except ImportError:
        from tkinter import messagebox
        messagebox.showerror("Missing Dependency", "Please install Pillow: pip install pillow")
        sys.exit(1)
    
    root = tk.Tk()
    app = ImageLabelTool(root)
    root.mainloop()