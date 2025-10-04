#!/usr/bin/env python3
# Quick test script to verify the new "Back to First Image" button
import tkinter as tk
from tkinter import ttk

def test_navigation_layout():
    """Test the new navigation button layout with Back to First Image"""
    root = tk.Tk()
    root.title("Navigation Layout Test")
    root.geometry("900x600")
    
    # Main content area
    content_frame = tk.Frame(root, bg="#FAFAFA")
    content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # Configure grid weights - 60:40 image:stats
    content_frame.grid_columnconfigure(0, weight=3)  # Image area: 60%
    content_frame.grid_columnconfigure(1, weight=2)  # Stats area: 40%
    content_frame.grid_rowconfigure(0, weight=1)
    
    # Center panel for image
    center_panel = tk.Frame(content_frame, bg="#E3F2FD", relief="solid", bd=2)
    center_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    
    # Add title
    tk.Label(center_panel, text="IMAGE DISPLAY AREA", bg="#E3F2FD", 
            font=("Arial", 16, "bold")).pack(pady=20)
    
    # Navigation buttons section (similar to actual layout)
    nav_label_container = tk.Frame(center_panel, bg="#E3F2FD")
    nav_label_container.pack(pady=(0, 20))
    
    # Previous buttons (left side) - stacked vertically
    prev_buttons_frame = tk.Frame(nav_label_container, bg="#E3F2FD")
    prev_buttons_frame.pack(side=tk.LEFT, padx=(0, 15))
    
    # Previous button (top)
    btn_prev = tk.Button(prev_buttons_frame, text="<< Prev", 
                        bg="#90CAF9", fg="white", font=("Arial", 10, "bold"),
                        padx=8, pady=3, relief="flat", state="normal")
    btn_prev.pack(pady=(0, 2))
    
    # Back to First Image button (bottom)
    btn_first = tk.Button(prev_buttons_frame, text="Back to First Image",
                         bg="#FF9800", fg="white", font=("Arial", 9, "bold"),
                         padx=6, pady=2, relief="flat", state="normal")
    btn_first.pack()
    
    # Label area (center) - simulated
    label_frame = tk.Frame(nav_label_container, bg="#FAFAFA", relief="solid", bd=1, 
                          padx=20, pady=15)
    label_frame.pack(side=tk.LEFT)
    tk.Label(label_frame, text="RADIO BUTTON\nLABELS AREA", bg="#FAFAFA", 
            font=("Arial", 12, "bold")).pack()
    
    # Next buttons (right side) - stacked vertically
    next_buttons_frame = tk.Frame(nav_label_container, bg="#E3F2FD")
    next_buttons_frame.pack(side=tk.RIGHT, padx=(8, 0))
    
    # Next button (top)
    btn_next = tk.Button(next_buttons_frame, text="Next >>",
                        bg="#90CAF9", fg="white", font=("Arial", 10, "bold"),
                        padx=8, pady=3, relief="flat", state="normal")
    btn_next.pack(pady=(0, 2))
    
    # Jump to Next Unclassified button (bottom)
    btn_jump = tk.Button(next_buttons_frame, text="Jump to Next Unclassified",
                        bg="#FF9800", fg="white", font=("Arial", 9, "bold"),
                        padx=6, pady=2, relief="flat", state="normal")
    btn_jump.pack()
    
    # Stats panel (right side)
    right_panel = tk.Frame(content_frame, bg="#FFF3E0", relief="solid", bd=2)
    right_panel.grid(row=0, column=1, sticky="nsew")
    tk.Label(right_panel, text="STATISTICS\nTABBED AREA", bg="#FFF3E0", 
            font=("Arial", 14, "bold")).pack(expand=True)
    
    # Add layout description
    description = tk.Label(root, 
        text="NEW NAVIGATION LAYOUT:\n" +
             "Left: [Prev] + [Back to First] | Center: Radio Buttons | Right: [Next] + [Jump to Unclassified]\n" +
             "Keyboard: Home key → Back to First Image",
        font=("Arial", 10), bg="lightgreen", pady=5)
    description.pack(side=tk.BOTTOM, fill=tk.X)
    
    root.mainloop()

if __name__ == "__main__":
    print("Testing navigation layout with 'Back to First Image' button...")
    test_navigation_layout()
    print("Navigation layout test completed!")