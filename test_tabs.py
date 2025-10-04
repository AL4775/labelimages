#!/usr/bin/env python3
# Quick test script to verify tabbed interface works
import tkinter as tk
from tkinter import ttk

def test_tabbed_layout():
    """Test the new tabbed statistics layout"""
    root = tk.Tk()
    root.title("Tabbed Layout Test")
    root.geometry("1000x700")
    
    # Main content area
    content_frame = tk.Frame(root, bg="#FAFAFA")
    content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # Configure grid weights - 60:40 image:stats
    content_frame.grid_columnconfigure(0, weight=3)  # Image area: 60%
    content_frame.grid_columnconfigure(1, weight=2)  # Stats area: 40%
    content_frame.grid_rowconfigure(0, weight=1)
    
    # Image panel (60% width)
    center_panel = tk.Frame(content_frame, bg="#E3F2FD", relief="solid", bd=2)
    center_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    tk.Label(center_panel, text="IMAGE DISPLAY\n(60% width)", bg="#E3F2FD", 
            font=("Arial", 16, "bold")).pack(expand=True)
    
    # Stats panel with tabs (40% width)
    right_panel = tk.Frame(content_frame, bg="#FAFAFA")
    right_panel.grid(row=0, column=1, sticky="nsew")
    
    # Create tabbed notebook for statistics
    stats_notebook = ttk.Notebook(right_panel)
    stats_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # TAB 1: Progress & Counts
    progress_tab = tk.Frame(stats_notebook, bg="#FAFAFA")
    stats_notebook.add(progress_tab, text="Progress")
    
    progress_frame = tk.Frame(progress_tab, bg="#F5F5F5", relief="solid", bd=1)
    progress_frame.pack(fill=tk.X, padx=5, pady=5)
    tk.Label(progress_frame, text="Progress Section", bg="#F5F5F5", 
            font=("Arial", 12, "bold"), fg="#5E88D8").pack(pady=5)
    tk.Label(progress_frame, text="Progress info goes here...", bg="#F5F5F5").pack(pady=5)
    
    counts_frame = tk.Frame(progress_tab, bg="#F5F5F5", relief="solid", bd=1)
    counts_frame.pack(fill=tk.X, padx=5, pady=5)
    tk.Label(counts_frame, text="Image Counts", bg="#F5F5F5", 
            font=("Arial", 12, "bold"), fg="#81C784").pack(pady=5)
    tk.Label(counts_frame, text="Counts info goes here...", bg="#F5F5F5").pack(pady=5)
    
    # TAB 2: Analysis
    analysis_tab = tk.Frame(stats_notebook, bg="#FAFAFA")
    stats_notebook.add(analysis_tab, text="Analysis")
    
    parcel_frame = tk.Frame(analysis_tab, bg="#F5F5F5", relief="solid", bd=1)
    parcel_frame.pack(fill=tk.X, padx=5, pady=5)
    tk.Label(parcel_frame, text="Parcel Count", bg="#F5F5F5", 
            font=("Arial", 12, "bold"), fg="#81C784").pack(pady=5)
    tk.Label(parcel_frame, text="Parcel stats go here...", bg="#F5F5F5").pack(pady=5)
    
    net_frame = tk.Frame(analysis_tab, bg="#F5F5F5", relief="solid", bd=1)
    net_frame.pack(fill=tk.X, padx=5, pady=5)
    tk.Label(net_frame, text="Net Stats", bg="#F5F5F5", 
            font=("Arial", 12, "bold"), fg="#5E88D8").pack(pady=5)
    tk.Label(net_frame, text="Net stats go here...", bg="#F5F5F5").pack(pady=5)
    
    # TAB 3: Monitor
    monitor_tab = tk.Frame(stats_notebook, bg="#FAFAFA")
    stats_notebook.add(monitor_tab, text="Monitor")
    
    auto_frame = tk.Frame(monitor_tab, bg="#FFF3E0", relief="solid", bd=1)
    auto_frame.pack(fill=tk.X, padx=5, pady=5)
    tk.Label(auto_frame, text="Auto Monitor New Files", bg="#FFF3E0", 
            font=("Arial", 12, "bold"), fg="#F57C00").pack(pady=5)
    tk.Label(auto_frame, text="Auto monitoring controls...", bg="#FFF3E0").pack(pady=5)
    
    # Add layout indicator
    tk.Label(root, text="TABBED LAYOUT: 60% Image | 40% Stats (3 Tabs: Progress, Analysis, Monitor)", 
            font=("Arial", 10, "bold"), bg="lightgreen").pack(side=tk.BOTTOM, fill=tk.X)
    
    root.mainloop()

if __name__ == "__main__":
    print("Testing tabbed statistics layout...")
    test_tabbed_layout()
    print("Tabbed layout test completed!")