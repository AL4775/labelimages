#!/usr/bin/env python3
"""
Quick test for the new chart functionality in Image Label Tool
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports
    print("Testing imports...")
    
    # Test basic imports
    import tkinter as tk
    from tkinter import ttk
    print("✓ tkinter imports OK")
    
    # Test chart imports
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import seaborn as sns
    print("✓ matplotlib/seaborn imports OK")
    
    # Test application import
    from image_label_tool import ImageLabelTool
    print("✓ ImageLabelTool import OK")
    
    # Test method existence
    root = tk.Tk()
    root.withdraw()  # Hide window
    app = ImageLabelTool(root)
    
    # Check if new methods exist
    assert hasattr(app, 'show_statistics_charts'), "show_statistics_charts method missing"
    assert hasattr(app, 'create_image_histogram'), "create_image_histogram method missing"  
    assert hasattr(app, 'create_parcel_pie_chart'), "create_parcel_pie_chart method missing"
    assert hasattr(app, 'create_progress_overview'), "create_progress_overview method missing"
    
    print("✓ All chart methods exist")
    
    # Check if button exists
    assert hasattr(app, 'btn_show_charts'), "Show Charts button missing"
    print("✓ Show Charts button exists")
    
    root.destroy()
    
    print("\n🎉 ALL TESTS PASSED!")
    print("The Image Label Tool is ready with fancy chart functionality!")
    print("\nTo use:")
    print("1. Run: python image_label_tool.py")
    print("2. Select a folder with images") 
    print("3. Classify some images")
    print("4. Click 'Show Charts' in the toolbar")
    print("5. Enjoy the fancy visualizations! 📊🥧📈")

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please install missing dependencies:")
    print("pip install matplotlib seaborn")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)