#!/usr/bin/env python3
"""
Manual test script to demonstrate False NoRead checkbox behavior
"""
import tkinter as tk
from tkinter import messagebox
import image_label_tool
import os

def demo_false_noread_behavior():
    """Demonstrate the False NoRead checkbox behavior"""
    
    # Check if there are any image files in the directory
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    current_dir = os.getcwd()
    
    # Look for any image files
    image_files = []
    for file in os.listdir(current_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    if not image_files:
        print("No image files found in the current directory.")
        print("To fully test the False NoRead feature:")
        print("1. Place some image files in this directory")
        print("2. Run: python image_label_tool.py")
        print("3. Test the following behavior:")
        print("   - Select any image and classify it as 'read failure'")
        print("   - Notice the False NoRead checkbox becomes enabled")
        print("   - Check the False NoRead checkbox")
        print("   - Change the classification to 'unreadable' or any other class")
        print("   - Notice the False NoRead checkbox becomes disabled and unchecked")
        print("   - Press 'F' key when classification is 'read failure' (should toggle)")
        print("   - Press 'F' key when classification is not 'read failure' (should do nothing)")
        return False
    
    print(f"Found {len(image_files)} image files:")
    for img in image_files[:5]:  # Show first 5
        print(f"  - {img}")
    if len(image_files) > 5:
        print(f"  ... and {len(image_files) - 5} more")
    
    print("\nTo test False NoRead checkbox behavior:")
    print("1. Run: python image_label_tool.py")
    print("2. Select any image")
    print("3. Test sequence:")
    print("   a) Classify as 'read failure' → checkbox should be ENABLED")
    print("   b) Check the False NoRead checkbox")
    print("   c) Change to 'unreadable' → checkbox should be DISABLED and UNCHECKED")
    print("   d) Change back to 'read failure' → checkbox should be ENABLED (but unchecked)")
    print("   e) Press 'F' key → should toggle checkbox (only works for 'read failure')")
    
    return True

if __name__ == "__main__":
    demo_false_noread_behavior()