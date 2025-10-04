#!/usr/bin/env python3
# Quick test script to verify layout changes work syntactically
import tkinter as tk

def test_layout():
    """Test the new layout structure without dependencies"""
    root = tk.Tk()
    root.title("Layout Test")
    root.geometry("1200x800")
    
    # Main content area
    content_frame = tk.Frame(root, bg="#FAFAFA")
    content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # Configure grid weights - NEW LAYOUT: 30% image, 70% stats
    content_frame.grid_columnconfigure(0, weight=1.5)  # Image area: 30%
    content_frame.grid_columnconfigure(1, weight=3.5)  # Stats area: 70%
    content_frame.grid_rowconfigure(0, weight=1)
    
    # Image panel (30% width)
    center_panel = tk.Frame(content_frame, bg="#E3F2FD", relief="solid", bd=2)
    center_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    tk.Label(center_panel, text="IMAGE DISPLAY\n(30% width)", bg="#E3F2FD", 
            font=("Arial", 16, "bold")).pack(expand=True)
    
    # Stats panel (70% width)
    right_panel = tk.Frame(content_frame, bg="#FAFAFA")
    right_panel.grid(row=0, column=1, sticky="nsew")
    
    # Configure stats panel grid for two columns
    right_panel.grid_columnconfigure(0, weight=1)  # Left stats
    right_panel.grid_columnconfigure(1, weight=1)  # Right stats
    right_panel.grid_rowconfigure(0, weight=1)
    
    # Left stats panel (Progress and Image Counts)
    left_stats_panel = tk.Frame(right_panel, bg="#E8F5E8", relief="solid", bd=2)
    left_stats_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
    tk.Label(left_stats_panel, text="Progress & Counts", bg="#E8F5E8", 
            font=("Arial", 12, "bold")).pack(pady=5)
    tk.Label(left_stats_panel, text="• Progress\n• Image Counts", bg="#E8F5E8", 
            font=("Arial", 10)).pack()
    
    # Right stats panel (Other stats)
    right_stats_panel = tk.Frame(right_panel, bg="#FFF3E0", relief="solid", bd=2)
    right_stats_panel.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
    tk.Label(right_stats_panel, text="Analysis & Monitoring", bg="#FFF3E0", 
            font=("Arial", 12, "bold")).pack(pady=5)
    tk.Label(right_stats_panel, text="• Parcel count\n• Net Stats\n• Auto Monitor", bg="#FFF3E0", 
            font=("Arial", 10)).pack()
    
    # Add width indicators
    tk.Label(root, text="NEW LAYOUT: 30% Image | 35% Progress/Counts | 35% Analysis/Monitoring", 
            font=("Arial", 10, "bold"), bg="yellow").pack(side=tk.BOTTOM, fill=tk.X)
    
    root.mainloop()

if __name__ == "__main__":
    print("Testing new layout structure...")
    test_layout()
    print("Layout test completed!")