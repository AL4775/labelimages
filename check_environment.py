#!/usr/bin/env python3
"""
Check which Python interpreter VS Code is using
"""
import sys
import os

print("=== VS CODE PYTHON ENVIRONMENT CHECK ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Check if we're in virtual environment
if '.venv' in sys.executable or 'venv' in sys.executable:
    print("OK: Using virtual environment")
else:
    print("ERROR: NOT using virtual environment - this will cause issues!")
    print("   Please select the correct Python interpreter in VS Code:")
    print("   Ctrl+Shift+P -> 'Python: Select Interpreter' -> .venv\\Scripts\\python.exe")

# Test critical imports
print("\n=== IMPORT TEST ===")
try:
    import matplotlib.pyplot as plt
    print("OK: matplotlib imports OK")
except Exception as e:
    print(f"ERROR: matplotlib import failed: {e}")

try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.destroy()
    print("OK: tkinter test OK")
except Exception as e:
    print(f"ERROR: tkinter test failed: {e}")

print("\n=== RECOMMENDATION ===")
if '.venv' not in sys.executable:
    print("FIX: Configure VS Code to use .venv\\Scripts\\python.exe")
    print("FIX: Or run: python run_vscode.py instead of image_label_tool.py")
else:
    print("SUCCESS: Environment is correctly configured!")
    print("INFO: You can now use 'Run Python File' on image_label_tool.py")