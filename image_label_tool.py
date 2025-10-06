import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime
import re
import random
import threading
import time
import cv2
import numpy as np
import logging
import multiprocessing

# Optional imports for charting functionality (DISABLED for stability)
HAS_MATPLOTLIB = False
# Charting functionality disabled to prevent executable issues
# try:
#     import matplotlib.pyplot as plt
#     import matplotlib.patches as patches
#     from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#     import seaborn as sns
#     HAS_MATPLOTLIB = True
# except ImportError:
#     pass

# Set to None since charting is disabled
plt = None
patches = None
FigureCanvasTkAgg = None
sns = None

# Application version
VERSION = "1.0.3"

LABELS = ["(Unclassified)", "no code", "read failure", "occluded", "image quality", "damaged", "other"]

class ImageLabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Image Label Tool v{VERSION}")
        self.root.configure(bg="#FAFAFA")  # Very light gray background
        self.root.minsize(800, 500)  # Ultra-compact minimum window size
        self.root.geometry("1000x600")  # Ultra-compact window size
        self.image_paths = []
        self.current_index = 0
        self.labels = {}
        self.folder_path = None
        self.csv_filename = None
        self.scale_1to1 = False  # Track if we're in 1:1 scale mode
        self.current_scale_factor = 1.0  # Track current scale factor
        self.zoom_level = 1.0  # Track zoom level for manual zoom
        self.pan_start_x = 0  # For mouse panning
        self.pan_start_y = 0  # For mouse panning
        
        # Track previously seen files for new file detection
        self.previously_seen_files = set()
        
        # Parcel index tracking
        self.parcel_indices = {}  # Maps parcel_id to parcel_index
        self.next_parcel_index = 1  # Next index to assign to a newly classified parcel
        
        # Set up logging for barcode detection
        self.setup_logging()
        
        # Set up proper cleanup when window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Chart update control (REMOVED - charts disabled)
        # self.chart_update_pending = False
        # self.charts_created = False
        
        # Chart figure references (REMOVED - charts disabled) 
        # self.histogram_figure = None
        # self.histogram_canvas = None
        # self.pie_figure = None
        # self.pie_canvas = None
        # self._last_chart_data = None
        
        self.setup_ui()

    def setup_logging(self):
        """Set up logging for barcode detection activities"""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create a timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(logs_dir, f'barcode_detection_{timestamp}.log')
        
        # Configure logging
        self.logger = logging.getLogger('BarcodeDetection')
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create console handler for debugging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log the start of the session
        self.logger.info("="*60)
        self.logger.info("BARCODE DETECTION LOG SESSION STARTED")
        self.logger.info("="*60)
        self.logger.info(f"Log file: {log_filename}")

    def setup_ui(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg="#FAFAFA", padx=8, pady=8)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Folder selection and total parcels
        top_frame = tk.Frame(main_frame, bg="#FAFAFA")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Folder selection
        self.btn_select = tk.Button(top_frame, text="Select Folder", command=self.select_folder,
                                  bg="#A5D6A7", fg="white", font=("Arial", 10, "bold"),
                                  padx=15, pady=6, relief="flat")
        self.btn_select.pack(side=tk.LEFT)
        
        # Folder path display
        self.folder_path_var = tk.StringVar(value="No folder selected")
        self.folder_path_label = tk.Label(top_frame, textvariable=self.folder_path_var, 
                                         bg="#FAFAFA", font=("Arial", 9), fg="#666666",
                                         wraplength=600, justify=tk.LEFT, anchor="w")
        self.folder_path_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Total number of parcels input (right side)
        total_frame = tk.Frame(top_frame, bg="#FAFAFA")
        total_frame.pack(side=tk.RIGHT)
        tk.Label(total_frame, text="Total number of parcels:", bg="#FAFAFA", font=("Arial", 11)).pack(side=tk.LEFT)
        self.total_parcels_var = tk.StringVar()
        self.total_parcels_entry = tk.Entry(total_frame, textvariable=self.total_parcels_var, width=8,
                                          font=("Arial", 11), bg="white", relief="solid", bd=1)
        self.total_parcels_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.total_parcels_entry.bind('<KeyRelease>', self.on_total_changed)
        
        # Filter dropdown (center)
        filter_frame = tk.Frame(top_frame, bg="#FAFAFA")
        filter_frame.pack(side=tk.LEFT, padx=(20, 0))
        tk.Label(filter_frame, text="Filter:", bg="#FAFAFA", font=("Arial", 10)).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="(Unclassified) only")
        filter_options = ["All images", "(Unclassified) only", "no code only", "read failure only", "occluded only", "image quality only", "damaged only", "other only"]
        self.filter_menu = tk.OptionMenu(filter_frame, self.filter_var, *filter_options, command=self.on_filter_changed)
        self.filter_menu.config(bg="#F5F5F5", font=("Arial", 10), relief="solid", bd=1)
        self.filter_menu.pack(side=tk.LEFT, padx=(5, 0))

        # Top toolbar for view controls and export
        toolbar_frame = tk.Frame(main_frame, bg="#E8E8E8", relief="solid", bd=1)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Scale info (compact display)
        self.scale_info_var = tk.StringVar()
        self.scale_info_label = tk.Label(toolbar_frame, textvariable=self.scale_info_var, 
                                       bg="#E8E8E8", font=("Arial", 10), fg="#757575")
        self.scale_info_label.pack(side=tk.LEFT, padx=(10, 15))
        
        # 1:1 Scale button
        self.btn_1to1 = tk.Button(toolbar_frame, text="1:1 Scale", command=self.toggle_1to1_scale,
                                bg="#FFCC80", fg="white", font=("Arial", 10, "bold"),
                                padx=8, pady=3, relief="flat")
        self.btn_1to1.pack(side=tk.LEFT, padx=(0, 10))
        
        # Zoom controls
        tk.Label(toolbar_frame, text="Zoom:", bg="#E8E8E8", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_zoom_out = tk.Button(toolbar_frame, text="−", command=self.zoom_out,
                                    bg="#CE93D8", fg="white", font=("Arial", 12, "bold"),
                                    padx=6, pady=2, relief="flat", width=2)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=(0, 3))
        
        self.btn_zoom_in = tk.Button(toolbar_frame, text="+", command=self.zoom_in,
                                   bg="#CE93D8", fg="white", font=("Arial", 12, "bold"),
                                   padx=6, pady=2, relief="flat", width=2)
        self.btn_zoom_in.pack(side=tk.LEFT, padx=(0, 15))

        # Export button for current filter
        self.btn_gen_filter_folder = tk.Button(toolbar_frame, text="Gen Filter Folder", 
                                             command=self.generate_filter_folder,
                                             bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
                                             padx=8, pady=3, relief="flat")
        self.btn_gen_filter_folder.pack(side=tk.LEFT, padx=(0, 10))

        # Main content area - horizontal layout (now without left panel)
        content_frame = tk.Frame(main_frame, bg="#FAFAFA")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure content_frame grid weights for proportional layout
        content_frame.grid_columnconfigure(0, weight=3)  # Image area: 60% of width
        content_frame.grid_columnconfigure(1, weight=2)  # Stats area: 40% of width
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Center panel for image
        center_panel = tk.Frame(content_frame, bg="#FAFAFA")
        center_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        
        # Right panel for statistics with tabbed interface
        right_panel = tk.Frame(content_frame, bg="#FAFAFA")
        right_panel.grid(row=0, column=1, sticky="nsew")

        # === CENTER PANEL: Image Display ===
        # Status indicator centered above image
        status_frame = tk.Frame(center_panel, bg="#FAFAFA")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.label_status_var = tk.StringVar()
        self.label_status_label = tk.Label(status_frame, textvariable=self.label_status_var, bg="#FAFAFA",
                                         font=("Arial", 14, "bold"))
        self.label_status_label.pack()
        
        # Image display area
        image_frame = tk.Frame(center_panel, bg="#FAFAFA")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create canvas with scrollbars for image display
        self.canvas = tk.Canvas(image_frame, bg="#FAFAFA", relief="solid", bd=2)
        
        # Scrollbars
        self.h_scrollbar = tk.Scrollbar(image_frame, orient="horizontal", command=self.canvas.xview)
        self.v_scrollbar = tk.Scrollbar(image_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights for image frame
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)

        # Bind mouse events for panning
        self.canvas.bind("<Button-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.mouse_wheel_zoom)
        
        # Add file status above label buttons - reduced spacing
        self.status_var = tk.StringVar()
        self.status = tk.Label(center_panel, textvariable=self.status_var, bg="#FAFAFA", 
                             font=("Arial", 12), fg="#424242")  # Smaller font
        self.status.pack(pady=(5, 2))  # Reduced from (10, 5) to (5, 2)
        
        # Add parcel index display - reduced spacing
        self.parcel_index_var = tk.StringVar()
        self.parcel_index_label = tk.Label(center_panel, textvariable=self.parcel_index_var, bg="#FAFAFA",
                                         font=("Arial", 12), fg="#424242")  # Smaller font
        self.parcel_index_label.pack(pady=(0, 2))  # Reduced from (0, 5) to (0, 2)

        # Navigation and radio buttons for labels (below image) - compact spacing
        self.label_var = tk.StringVar(value=LABELS[0])
        
        # Main container for navigation and labels
        nav_label_container = tk.Frame(center_panel, bg="#FAFAFA")
        nav_label_container.pack(pady=(0, 5))  # Reduced from 10 to 5
        
        # Previous buttons (left side) - stacked vertically for consistency
        prev_buttons_frame = tk.Frame(nav_label_container, bg="#FAFAFA")
        prev_buttons_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Previous button (top)
        self.btn_prev = tk.Button(prev_buttons_frame, text="<< Prev", command=self.prev_image,
                                bg="#90CAF9", fg="white", font=("Arial", 10, "bold"),
                                padx=8, pady=3, relief="flat")
        self.btn_prev.pack(pady=(0, 2))  # Small gap between buttons
        
        # First Image button (bottom)
        self.btn_first = tk.Button(prev_buttons_frame, text="First Image", 
                                  command=self.go_to_first_image,
                                  bg="#FF9800", fg="white", font=("Arial", 9, "bold"),  # Smaller font
                                  padx=6, pady=2, relief="flat")  # Smaller padding
        self.btn_first.pack()
        
        # Label frame (center)
        label_frame = tk.Frame(nav_label_container, bg="#FAFAFA", relief="solid", bd=1, padx=10, pady=6)  # Reduced padding
        label_frame.pack(side=tk.LEFT)
        
        radio_container = tk.Frame(label_frame, bg="#FAFAFA")
        radio_container.pack()
        
        label_colors = {
            "(Unclassified)": "#F5F5F5", 
            "no code": "#FFF3E0", 
            "read failure": "#FCE4EC", 
            "occluded": "#E3F2FD",
            "image quality": "#F1F8E9",
            "damaged": "#FFF8E1",
            "other": "#F3E5F5"
        }
        
        # Add keyboard shortcuts to labels
        label_shortcuts = {
            "(Unclassified)": "",
            "no code": " (Q)",
            "read failure": " (W)", 
            "occluded": " (E)",
            "image quality": " (R)",
            "damaged": " (T)",
            "other": " (Y)"
        }
        
        self.radio_buttons = []  # Store radio buttons for enabling/disabling
        
        # Single row layout with multi-line text for compact width
        for i, label in enumerate(LABELS):
            display_text = label + label_shortcuts[label]
            # Format multi-word labels with line breaks
            if " " in label and label != "(Unclassified)":
                words = display_text.split(" ")
                if len(words) >= 2:
                    # Split into 2 lines for better compactness
                    mid_point = len(words) // 2
                    line1 = " ".join(words[:mid_point])
                    line2 = " ".join(words[mid_point:])
                    display_text = f"{line1}\n{line2}"
            
            rb = tk.Radiobutton(radio_container, text=display_text, variable=self.label_var, 
                              value=label, command=self.set_label_radio,
                              bg=label_colors[label], font=("Arial", 11, "bold"),
                              selectcolor="white", padx=2, pady=1, 
                              justify=tk.CENTER)  # Center-align multi-line text
            rb.grid(row=0, column=i, padx=1, pady=1, sticky="ew")  # Single row layout
            self.radio_buttons.append(rb)
        
        # Navigation buttons (right side) - stacked vertically for width efficiency
        nav_buttons_frame = tk.Frame(nav_label_container, bg="#FAFAFA")
        nav_buttons_frame.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Next button (top)
        self.btn_next = tk.Button(nav_buttons_frame, text="Next >>", command=self.next_image,
                                bg="#90CAF9", fg="white", font=("Arial", 10, "bold"),
                                padx=8, pady=3, relief="flat")
        self.btn_next.pack(pady=(0, 2))  # Small gap between buttons
        
        # Next Unclassified button (bottom)
        self.btn_jump_unclassified = tk.Button(nav_buttons_frame, text="Next Unclass", 
                                              command=self.jump_to_next_unclassified,
                                              bg="#FF9800", fg="white", font=("Arial", 9, "bold"),  # Smaller font
                                              padx=6, pady=2, relief="flat")  # Smaller padding
        self.btn_jump_unclassified.pack()

        # === RIGHT PANEL: Statistics with Tabs ===
        # Create tabbed notebook for statistics
        stats_notebook = ttk.Notebook(right_panel)
        stats_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === TAB 1: Progress & Counts ===
        progress_tab = tk.Frame(stats_notebook, bg="#FAFAFA")
        stats_notebook.add(progress_tab, text="Progress")
        
        # Progress section
        progress_section = tk.Frame(progress_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        progress_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(progress_section, text="Progress", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#5E88D8").pack()
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(progress_section, textvariable=self.progress_var, bg="#F5F5F5",
                                     font=("Arial", 13), fg="#424242", wraplength=200, 
                                     justify=tk.LEFT, anchor="w")
        self.progress_label.pack(pady=(0, 0), fill=tk.X)
        
        # Image counts section
        counts_section = tk.Frame(progress_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        counts_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(counts_section, text="Image Counts", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#81C784").pack()
        self.count_var = tk.StringVar()
        self.count_label = tk.Label(counts_section, textvariable=self.count_var, bg="#F5F5F5",
                                  font=("Arial", 13), fg="#424242", wraplength=200,
                                  justify=tk.LEFT, anchor="w")
        self.count_label.pack(pady=(3, 0), fill=tk.X)
        
        # Auto monitoring section (moved from Monitor tab)
        auto_detect_section = tk.Frame(progress_tab, bg="#FFF3E0", relief="solid", bd=1, padx=6, pady=6)
        auto_detect_section.pack(fill=tk.X, pady=(0, 6))
        
        # === TAB 2: Analysis ===
        analysis_tab = tk.Frame(stats_notebook, bg="#FAFAFA")
        stats_notebook.add(analysis_tab, text="Analysis")
        
        # Warning message for incomplete classification (in Analysis tab)
        self.warning_message_label = tk.Label(analysis_tab, 
                                            text="⚠️ Warning: still remaining images to classify. The statistics may be inaccurate.",
                                            bg="#FAFAFA", fg="#FF0000", font=("Arial", 12, "bold"),
                                            wraplength=250, justify=tk.LEFT)
        self.warning_message_label.pack(pady=(5, 10), fill=tk.X)
        self.warning_message_label.pack_forget()  # Initially hidden
        
        # Parcel statistics section
        parcel_section = tk.Frame(analysis_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        parcel_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(parcel_section, text="Parcel count", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#81C784").pack()
        self.parcel_count_var = tk.StringVar()
        self.parcel_count_label = tk.Label(parcel_section, textvariable=self.parcel_count_var, 
                                         font=("Arial", 13), bg="#F5F5F5", fg="#424242", wraplength=200,
                                         justify=tk.LEFT, anchor="w")
        self.parcel_count_label.pack(pady=(3, 0), fill=tk.X)
        
        # Total statistics section
        total_section = tk.Frame(analysis_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        total_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(total_section, text="Net Stats", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#5E88D8").pack()
        self.parcel_stats_var = tk.StringVar()
        self.parcel_stats_label = tk.Label(total_section, textvariable=self.parcel_stats_var, 
                                         font=("Arial", 13), fg="#424242", bg="#F5F5F5", wraplength=200,
                                         justify=tk.LEFT, anchor="w")
        self.parcel_stats_label.pack(pady=(3, 0), fill=tk.X)

        # Auto monitoring section content (now in Progress tab)
        tk.Label(auto_detect_section, text="Auto Monitor New Files", bg="#FFF3E0", font=("Arial", 12, "bold"), fg="#F57C00").pack()
        
        # Checkbox for auto barcode detection on new files (HIDDEN)
        self.auto_detect_enabled = tk.BooleanVar(value=False)
        self.auto_detect_checkbox = tk.Checkbutton(auto_detect_section, 
                                                 text="Auto detect barcodes on new files",
                                                 variable=self.auto_detect_enabled,
                                                 bg="#FFF3E0", font=("Arial", 12),
                                                 anchor="w", justify="left")
        # self.auto_detect_checkbox.pack(pady=(10, 5), fill=tk.X)  # HIDDEN: Comment out the pack() call
        
        # Progress indicator for auto classification
        self.auto_detect_progress_var = tk.StringVar()
        self.auto_detect_progress_label = tk.Label(auto_detect_section, textvariable=self.auto_detect_progress_var,
                                                 bg="#FFF3E0", font=("Arial", 13), fg="#424242", wraplength=220,
                                                 justify=tk.LEFT, anchor="w")
        self.auto_detect_progress_label.pack(fill=tk.X)
        
        # Auto-timer controls
        timer_frame = tk.Frame(auto_detect_section, bg="#FFF3E0")
        timer_frame.pack(pady=(10, 0))
        
        self.auto_timer_enabled = tk.BooleanVar()
        self.auto_timer_button = tk.Button(timer_frame, text="Start", 
                                          command=self.toggle_auto_timer,
                                          bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                                          activebackground="#45a049", width=6)
        self.auto_timer_button.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(timer_frame, text="every", bg="#FFF3E0", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.auto_timer_interval = tk.StringVar(value="10")
        
        # Register validation function for numeric input
        vcmd = (self.root.register(self.validate_numeric_input), '%P')
        
        self.auto_timer_entry = tk.Entry(timer_frame, textvariable=self.auto_timer_interval,
                                        width=5, font=("Arial", 12), justify="center",
                                        validate='key', validatecommand=vcmd)
        self.auto_timer_entry.pack(side=tk.LEFT, padx=(0, 2))
        
        tk.Label(timer_frame, text="min", bg="#FFF3E0", font=("Arial", 12)).pack(side=tk.LEFT)
        
        # Auto-timer status
        self.auto_timer_status_var = tk.StringVar()
        self.auto_timer_status_label = tk.Label(auto_detect_section, textvariable=self.auto_timer_status_var,
                                               bg="#FFF3E0", font=("Arial", 11), fg="#666666", wraplength=220,
                                               justify=tk.LEFT, anchor="w")
        self.auto_timer_status_label.pack(pady=(5, 0), fill=tk.X)
        
        # Initialize timer variables
        self.auto_timer_job = None
        self.last_auto_run = None
        self.countdown_job = None
        self.countdown_end_time = None

        # Bind window resize event to update image display
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Bind keyboard shortcuts for labeling
        self.root.bind('<KeyPress-q>', self.label_shortcut_q)
        self.root.bind('<KeyPress-Q>', self.label_shortcut_q)
        self.root.bind('<KeyPress-w>', self.label_shortcut_w)
        self.root.bind('<KeyPress-W>', self.label_shortcut_w)
        self.root.bind('<KeyPress-e>', self.label_shortcut_e)
        self.root.bind('<KeyPress-E>', self.label_shortcut_e)
        self.root.bind('<KeyPress-r>', self.label_shortcut_r)
        self.root.bind('<KeyPress-R>', self.label_shortcut_r)
        self.root.bind('<KeyPress-t>', self.label_shortcut_t)
        self.root.bind('<KeyPress-T>', self.label_shortcut_t)
        self.root.bind('<KeyPress-y>', self.label_shortcut_y)
        self.root.bind('<KeyPress-Y>', self.label_shortcut_y)
        
        # Bind O/P keys for navigation (avoiding arrow key conflicts with radio buttons)
        self.root.bind('<KeyPress-o>', self.prev_image_shortcut)
        self.root.bind('<KeyPress-O>', self.prev_image_shortcut)
        self.root.bind('<KeyPress-p>', self.next_image_shortcut)
        self.root.bind('<KeyPress-P>', self.next_image_shortcut)
        
        # Bind Home key for go to first image
        self.root.bind('<Home>', self.go_to_first_image_shortcut)
        
        # Bind Shift+O for 1:1 scale
        self.root.bind('<Shift-O>', self.scale_1to1_shortcut)
        self.root.bind('<Shift-o>', self.scale_1to1_shortcut)
        
        # Bind Shift+W for fit-to-window
        self.root.bind('<Shift-W>', self.fit_window_shortcut)
        self.root.bind('<Shift-w>', self.fit_window_shortcut)
        
        # Set focus to root window to capture keyboard events
        self.root.focus_set()
        
        # Initialize button state based on default filter
        self.update_filter_button_state()

    def validate_numeric_input(self, new_value):
        """Validate that input contains only numbers and decimal points"""
        if new_value == "":
            return True  # Allow empty string for clearing
        try:
            float(new_value)
            return True
        except ValueError:
            return False

    def update_warning_message(self):
        """Update the warning message in Analysis tab based on classification status"""
        if not hasattr(self, 'warning_message_label'):
            return
            
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            self.warning_message_label.pack_forget()
            return
        
        # Count unclassified images
        unclassified_count = 0
        for path in self.all_image_paths:
            if path not in self.labels or self.labels[path] == "(Unclassified)":
                unclassified_count += 1
        
        if unclassified_count > 0:
            # Show warning message
            self.warning_message_label.pack(pady=(5, 10), fill=tk.X)
        else:
            # Hide warning message
            self.warning_message_label.pack_forget()

    def update_navigation_buttons(self):
        """Update the state of navigation buttons based on current position and available images"""
        if not hasattr(self, 'image_paths') or not self.image_paths:
            # No images loaded - disable all navigation buttons
            if hasattr(self, 'btn_prev'):
                self.btn_prev.config(state='disabled')
            if hasattr(self, 'btn_next'):
                self.btn_next.config(state='disabled')
            if hasattr(self, 'btn_jump_unclassified'):
                self.btn_jump_unclassified.config(state='disabled')
            return
        
        # Update Prev button
        if hasattr(self, 'btn_prev'):
            if self.current_index <= 0:
                self.btn_prev.config(state='disabled')
            else:
                self.btn_prev.config(state='normal')
        
        # Update Next button  
        if hasattr(self, 'btn_next'):
            if self.current_index >= len(self.image_paths) - 1:
                self.btn_next.config(state='disabled')
            else:
                self.btn_next.config(state='normal')
        
        # Update Next Unclassified button - only enabled when filter is "All images"
        if hasattr(self, 'btn_jump_unclassified'):
            filter_is_all = self.filter_var.get() == "All images"
            if not filter_is_all or not self.image_paths:
                self.btn_jump_unclassified.config(state='disabled')
            else:
                self.btn_jump_unclassified.config(state='normal')

    def on_closing(self):
        """Handle application cleanup before closing"""
        # Cancel any running timer jobs to prevent errors
        if hasattr(self, 'countdown_job') and self.countdown_job:
            self.root.after_cancel(self.countdown_job)
            self.countdown_job = None
        
        if hasattr(self, 'auto_timer_job') and self.auto_timer_job:
            self.root.after_cancel(self.auto_timer_job)
            self.auto_timer_job = None
        
        # Close the application
        self.root.destroy()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
        
        # Update the folder path display
        self.folder_path_var.set(f"Current folder: {folder}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = os.path.join(folder, f"revision_{timestamp}.csv")
        
        # Load all image files from the directory
        all_files = [f for f in os.listdir(folder)
                     if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
        
        self.all_image_paths = []
        for f in all_files:
            self.all_image_paths.append(os.path.join(folder, f))
        
        self.all_image_paths.sort()
        self.current_index = 0
        self.labels = {}  # Reset labels for new folder
        
        # Initialize previously seen files with current files
        self.previously_seen_files = set(self.all_image_paths)
        
        self.load_csv()  # Try to load existing CSV if any
        self.auto_detect_total_groups()  # Auto-detect total number of parcels from filenames
        self.apply_filter()  # Apply current filter to show appropriate images
        
        # Update warning message and navigation buttons
        self.update_warning_message()
        self.update_navigation_buttons()

    def show_image(self):
        if not self.image_paths:
            self.canvas.delete("all")
            self.status_var.set("No images loaded.")
            self.scale_info_var.set("")
            return
        path = self.image_paths[self.current_index]
        img = Image.open(path)
        original_width, original_height = img.size
        
        # Clear previous image
        self.canvas.delete("all")
        
        # Get canvas dimensions (reduced for ultra-compact layout)
        canvas_width = max(350, self.canvas.winfo_width())  # Reduced from 400
        canvas_height = max(250, self.canvas.winfo_height())  # Reduced from 300
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 350, 350  # Smaller default size
        
        if self.scale_1to1:
            # Show image at 1:1 scale with current zoom level
            scale_factor = self.zoom_level
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            if scale_factor != 1.0:
                display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                display_img = img
            
            self.current_scale_factor = scale_factor
            scale_text = f"Scale: {scale_factor:.2f}\n({scale_factor*100:.1f}%)"
            
            # Set scroll region to image size
            self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
            
            if new_width > canvas_width or new_height > canvas_height:
                scale_text += "\nUse mouse to pan"
                # Show scrollbars
                self.h_scrollbar.grid(row=1, column=0, sticky="ew")
                self.v_scrollbar.grid(row=0, column=1, sticky="ns")
            else:
                # Hide scrollbars if not needed
                self.h_scrollbar.grid_remove()
                self.v_scrollbar.grid_remove()
        else:
            # Calculate scale factor needed to fit image (fitted mode)
            scale_x = canvas_width / original_width
            scale_y = canvas_height / original_height
            scale_factor = min(scale_x, scale_y)
            self.current_scale_factor = scale_factor
            self.zoom_level = scale_factor  # Sync zoom level with fitted scale
            
            # Resize image to fit available space while maintaining aspect ratio
            display_img = img.copy()
            display_img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            scale_text = f"Scale: {scale_factor:.2f}\n({scale_factor*100:.1f}%)\nFitted to window"
            
            # Reset scroll region for fitted mode and center the image
            img_width, img_height = display_img.size
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            # Hide scrollbars in fitted mode
            self.h_scrollbar.grid_remove()
            self.v_scrollbar.grid_remove()
        
        self.tk_img = ImageTk.PhotoImage(display_img)
        
        # Center the image in the canvas
        img_width, img_height = display_img.size
        if self.scale_1to1:
            # For 1:1 mode, place image at origin for proper scrolling
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        else:
            # For fitted mode, center the image
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            self.canvas.create_image(center_x, center_y, anchor="center", image=self.tk_img)
        
        self.scale_info_var.set(scale_text)
        
        label = self.labels.get(path, LABELS[0])
        self.label_var.set(label)
        self.status_var.set(f"{os.path.basename(path)} ({self.current_index+1}/{len(self.image_paths)}) - {original_width}x{original_height}px")
        
        # Update progress and label status
        self.update_progress_display()
        self.update_current_label_status()
        self.update_parcel_index_display()
        
        # Update navigation buttons
        self.update_navigation_buttons()

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            # Reset to fit mode when navigating to new image
            self.reset_to_fit_mode()
            self.show_image()

    def go_to_first_image(self):
        """Jump to the first image in the list."""
        if self.image_paths and self.current_index > 0:
            self.current_index = 0
            # Reset to fit mode when navigating to new image
            self.reset_to_fit_mode()
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            # Reset to fit mode when navigating to new image
            self.reset_to_fit_mode()
            self.show_image()

    def jump_to_next_unclassified(self):
        """Jump to the next unclassified image after the current index."""
        if not self.image_paths:
            return
        
        # Start searching from the next image after current
        start_index = (self.current_index + 1) % len(self.image_paths)
        
        # Search for the next unclassified image
        for i in range(len(self.image_paths)):
            check_index = (start_index + i) % len(self.image_paths)
            path = self.image_paths[check_index]
            
            # Check if image is unclassified
            if path not in self.labels or self.labels[path] == "(Unclassified)":
                self.current_index = check_index
                self.show_image()
                return
        
        # If no unclassified images found, show a message
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Navigation", "No unclassified images found.")

    def set_label(self, value):
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        self.labels[path] = value
        self.save_csv()
        self.update_counts()

    def set_label_radio(self):
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        
        # Assign parcel index if this is the first classification for this parcel
        self.assign_parcel_index_if_needed(path)
        
        self.labels[path] = self.label_var.get()
        self.save_csv()
        self.update_counts()
        self.update_parcel_stats()
        self.update_total_stats()
        self.update_progress_display()
        self.update_current_label_status()
        self.update_parcel_index_display()
        
        # If filtering is active, reapply filter in case current image no longer matches
        if self.filter_var.get() != "All images":
            current_path = path
            current_index_before_filter = self.current_index
            self.apply_filter()
            
            # Try to find the image we were just on first
            if current_path in self.image_paths:
                self.current_index = self.image_paths.index(current_path)
                self.show_image()
            else:
                # Image no longer matches filter, find next appropriate image
                # Look for the next image at or after the current position in the original list
                found_next = False
                
                # Get the original position in all_image_paths
                if current_path in self.all_image_paths:
                    original_position = self.all_image_paths.index(current_path)
                    
                    # Look for the next image in all_image_paths that's also in filtered list
                    for i in range(original_position + 1, len(self.all_image_paths)):
                        if self.all_image_paths[i] in self.image_paths:
                            self.current_index = self.image_paths.index(self.all_image_paths[i])
                            found_next = True
                            break
                
                # If no image found after current position, wrap around to beginning
                if not found_next and self.image_paths:
                    self.current_index = 0
                elif not self.image_paths:
                    # No images match filter anymore
                    self.current_index = 0
                
                self.show_image()

    def assign_parcel_index_if_needed(self, image_path):
        """Assign a parcel index to a parcel when it gets its first classification"""
        parcel_id = self.get_parcel_number(image_path)
        if not parcel_id:
            return  # No parcel ID, can't assign index
            
        # Check if this parcel already has an index
        if parcel_id in self.parcel_indices:
            return  # Already has an index
            
        # Check if this parcel has any classified images (other than the current one being set)
        parcel_has_classified_images = False
        for path in self.all_image_paths:
            if self.get_parcel_number(path) == parcel_id and path != image_path:
                if path in self.labels and self.labels[path] != "(Unclassified)":
                    parcel_has_classified_images = True
                    break
        
        # If this is the first classification for this parcel, assign an index
        if not parcel_has_classified_images:
            self.parcel_indices[parcel_id] = self.next_parcel_index
            self.next_parcel_index += 1

    def get_parcel_index(self, image_path):
        """Get the parcel index for an image, or None if parcel is unclassified"""
        parcel_id = self.get_parcel_number(image_path)
        if not parcel_id:
            return None
        return self.parcel_indices.get(parcel_id, None)

    def label_shortcut_q(self, event=None):
        """Keyboard shortcut: Q for 'no code'"""
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("no code")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_w(self, event=None):
        """Keyboard shortcut: W for 'read failure'"""
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("read failure")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_e(self, event=None):
        """Keyboard shortcut: E for 'occluded'"""
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("occluded")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_r(self, event=None):
        """Keyboard shortcut: R for 'image quality'"""
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("image quality")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_t(self, event=None):
        """Keyboard shortcut: T for 'damaged'"""
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("damaged")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_y(self, event=None):
        """Keyboard shortcut: Y for 'other'"""
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("other")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def prev_image_shortcut(self, event=None):
        """Keyboard shortcut: Left arrow for previous image"""
        self.prev_image()

    def next_image_shortcut(self, event=None):
        """Keyboard shortcut: Right arrow for next image"""
        self.next_image()

    def go_to_first_image_shortcut(self, event=None):
        """Keyboard shortcut: Home key for go to first image"""
        self.go_to_first_image()

    def scale_1to1_shortcut(self, event=None):
        """Keyboard shortcut: Shift+O for 1:1 scale (always force true 1:1)"""
        # Always force to true 1:1 scale regardless of current state
        self.scale_1to1 = True
        self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
        self.zoom_level = 1.0  # Force reset zoom level to true 1:1
        # Always refresh the current image display to apply true 1:1 scale
        if hasattr(self, 'image_paths') and self.image_paths:
            self.show_image()

    def fit_window_shortcut(self, event=None):
        """Keyboard shortcut: Shift+W for fit-to-window (always set to fit)"""
        # Always set to fit mode regardless of current state
        if self.scale_1to1:
            self.scale_1to1 = False
            self.zoom_level = 1.0
            self.btn_1to1.config(text="1:1 Scale", bg="#FFCC80")
            # Refresh the current image display
            if hasattr(self, 'image_paths') and self.image_paths:
                self.show_image()

    def on_total_changed(self, event=None):
        """Called when the total parcels field changes"""
        self.update_total_stats()
        # Trigger CSV and stats refresh when total parcels changes
        self.save_csv()

    def on_filter_changed(self, value=None):
        """Called when the filter dropdown changes"""
        self.apply_filter()
        self.update_filter_button_state()

    def update_filter_button_state(self):
        """Enable/disable the filter folder generation button based on current filter"""
        if not hasattr(self, 'btn_gen_filter_folder'):
            return
            
        filter_value = self.filter_var.get()
        
        # Disable button for "All images" and "(Unclassified) only"
        if filter_value in ["All images", "(Unclassified) only"]:
            self.btn_gen_filter_folder.config(state='disabled', bg="#CCCCCC")
        else:
            self.btn_gen_filter_folder.config(state='normal', bg="#9C27B0")

    def apply_filter(self):
        """Apply the current filter to show appropriate images"""
        if not hasattr(self, 'all_image_paths'):
            return
            
        filter_value = self.filter_var.get()
        
        if filter_value == "All images":
            self.image_paths = self.all_image_paths.copy()
        else:
            # Map filter names to label values
            filter_map = {
                "(Unclassified) only": "(Unclassified)",
                "no code only": "no code",
                "read failure only": "read failure",
                "occluded only": "occluded",
                "image quality only": "image quality",
                "damaged only": "damaged",
                "other only": "other"
            }
            
            target_label = filter_map.get(filter_value)
            if target_label:
                self.image_paths = [path for path in self.all_image_paths 
                                  if self.labels.get(path, LABELS[0]) == target_label]
            else:
                self.image_paths = self.all_image_paths.copy()
        
        # Reset to first image and update display
        self.current_index = 0
        self.show_image()
        self.update_counts()
        self.update_parcel_stats()
        self.update_total_stats()
        self.update_progress_display()
        if self.image_paths:  # Only update if there are images loaded
            self.update_parcel_index_display()
        
        # Update navigation buttons
        self.update_navigation_buttons()

    def load_csv(self):
        # Reset parcel indices when loading
        self.parcel_indices = {}
        self.next_parcel_index = 1
        
        if not self.csv_filename or not os.path.exists(self.csv_filename):
            # Try to find existing revision CSV files in the folder
            if self.folder_path:
                existing_csvs = [f for f in os.listdir(self.folder_path) 
                               if f.startswith("revision_") and f.endswith(".csv")]
                if existing_csvs:
                    # Parse timestamps and find the most recent one
                    most_recent_file = None
                    most_recent_time = None
                    
                    for csv_file in existing_csvs:
                        try:
                            # Extract timestamp from filename: revision_YYYYMMDD_HHMMSS.csv
                            timestamp_str = csv_file[9:-4]  # Remove "revision_" and ".csv"
                            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            if most_recent_time is None or timestamp > most_recent_time:
                                most_recent_time = timestamp
                                most_recent_file = csv_file
                        except ValueError:
                            # Skip files that don't match the expected format
                            continue
                    
                    if most_recent_file:
                        existing_csv = os.path.join(self.folder_path, most_recent_file)
                        self._load_csv_file(existing_csv)
            return
        self._load_csv_file(self.csv_filename)

    def _load_csv_file(self, filepath):
        """Helper method to load CSV file and restore parcel indices"""
        max_parcel_index = 0
        
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Read header
            
            for row in reader:
                if len(row) >= 2:  # At minimum need image_path and image_label
                    image_path = row[0]
                    image_label = row[1]
                    self.labels[image_path] = image_label
                    
                    # If parcel_index column exists and has a value, restore the parcel index
                    if len(row) >= 5 and row[4]:  # parcel_index is 5th column (index 4)
                        try:
                            parcel_index = int(row[4])
                            parcel_id = self.get_parcel_number(image_path)
                            if parcel_id:
                                self.parcel_indices[parcel_id] = parcel_index
                                max_parcel_index = max(max_parcel_index, parcel_index)
                        except (ValueError, TypeError):
                            pass  # Skip invalid parcel index values
        
        # Set next_parcel_index to be one more than the highest existing index
        self.next_parcel_index = max_parcel_index + 1

    def save_csv(self):
        if not self.csv_filename:
            return
        with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['image_path', 'image_label', 'parcel_number', 'parcel_label', 'parcel_index'])
            
            # Calculate current parcel labels
            parcel_labels_dict = self.calculate_parcel_labels()
            
            for path, label in self.labels.items():
                parcel_id = self.get_parcel_number(path)
                parcel_label = parcel_labels_dict.get(parcel_id, "no code") if parcel_id else "no code"
                parcel_index = self.get_parcel_index(path)
                writer.writerow([path, label, parcel_id or "", parcel_label, parcel_index or ""])
        
        # Also generate statistics CSV file
        self.save_stats_csv()

    def save_stats_csv(self):
        """Generate a statistics CSV file with all counting and parcel information"""
        if not self.csv_filename:
            return
            
        # Extract timestamp from the main CSV filename
        # Expected format: revision_YYYYMMDD_HHMMSS.csv
        base_name = os.path.basename(self.csv_filename)
        if base_name.startswith('revision_'):
            timestamp = base_name[9:-4]  # Extract timestamp part
            stats_filename = os.path.join(os.path.dirname(self.csv_filename), f"stats_{timestamp}.csv")
        else:
            # Fallback if filename format is different
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stats_filename = os.path.join(os.path.dirname(self.csv_filename), f"stats_{timestamp}.csv")
        
        # Calculate all statistics
        stats_data = self.calculate_comprehensive_stats()
        
        with open(stats_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write statistics header
            writer.writerow(['category', 'metric', 'value', 'description'])
            
            # Write all statistics
            for category, metrics in stats_data.items():
                for metric, data in metrics.items():
                    writer.writerow([category, metric, data['value'], data['description']])

    def calculate_comprehensive_stats(self):
        """Calculate comprehensive statistics for the stats CSV"""
        stats = {
            'Image_Counts': {},
            'Parcel_Counts': {},
            'Progress_Stats': {},
            'System_Info': {}
        }
        
        # Image counting statistics
        image_counts = {label: 0 for label in LABELS}
        total_images = 0
        
        if hasattr(self, 'all_image_paths') and self.all_image_paths:
            total_images = len(self.all_image_paths)
            for path in self.all_image_paths:
                if path in self.labels and self.labels[path] != "(Unclassified)":
                    label = self.labels[path]
                    if label in image_counts:
                        image_counts[label] += 1
                else:
                    image_counts["(Unclassified)"] += 1
        
        # Store image count statistics
        for label, count in image_counts.items():
            stats['Image_Counts'][label] = {
                'value': count,
                'description': f'Number of images classified as {label}'
            }
        
        stats['Image_Counts']['total_images'] = {
            'value': total_images,
            'description': 'Total number of images in dataset'
        }
        
        # Calculate parcel statistics
        parcel_labels_dict = self.calculate_parcel_labels()
        parcel_counts = {}
        unique_parcels = set()
        
        for path in self.all_image_paths if hasattr(self, 'all_image_paths') else []:
            parcel_id = self.get_parcel_number(path)
            if parcel_id:
                unique_parcels.add(parcel_id)
                parcel_label = parcel_labels_dict.get(parcel_id, "no code")
                parcel_counts[parcel_label] = parcel_counts.get(parcel_label, 0) + 1
        
        # Store parcel statistics
        for label, count in parcel_counts.items():
            stats['Parcel_Counts'][f'parcels_{label}'] = {
                'value': count,
                'description': f'Number of parcels classified as {label}'
            }
        
        stats['Parcel_Counts']['total_unique_parcels'] = {
            'value': len(unique_parcels),
            'description': 'Total number of unique parcels'
        }
        
        # Add total number of parcels (including duplicates/all parcel entries)
        total_parcel_entries = 0
        for path in self.all_image_paths if hasattr(self, 'all_image_paths') else []:
            if self.get_parcel_number(path):
                total_parcel_entries += 1
        
        stats['Parcel_Counts']['total_parcel_entries'] = {
            'value': total_parcel_entries,
            'description': 'Total number of parcel entries (including duplicates)'
        }
        
        # Add manually entered total number of parcels
        try:
            manual_total_parcels = int(self.total_parcels_var.get()) if hasattr(self, 'total_parcels_var') and self.total_parcels_var.get() else 0
        except ValueError:
            manual_total_parcels = 0
            
        stats['Parcel_Counts']['manual_total_parcels'] = {
            'value': manual_total_parcels,
            'description': 'Manually entered total number of parcels'
        }
        
        # Calculate progress statistics
        classified_images = sum(count for label, count in image_counts.items() if label != "(Unclassified)")
        unclassified_images = image_counts.get("(Unclassified)", 0)
        progress_percentage = (classified_images / total_images * 100) if total_images > 0 else 0
        
        stats['Progress_Stats']['classified_images'] = {
            'value': classified_images,
            'description': 'Number of images that have been classified'
        }
        
        stats['Progress_Stats']['unclassified_images'] = {
            'value': unclassified_images,
            'description': 'Number of images still unclassified'
        }
        
        stats['Progress_Stats']['progress_percentage'] = {
            'value': f'{progress_percentage:.1f}%',
            'description': 'Percentage of images classified'
        }
        
        # System information
        from datetime import datetime
        stats['System_Info']['timestamp'] = {
            'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Time when statistics were generated'
        }
        
        if hasattr(self, 'folder_path') and self.folder_path:
            stats['System_Info']['source_folder'] = {
                'value': self.folder_path,
                'description': 'Source folder path for images'
            }
        
        return stats

    def update_chart_tabs(self):
        """REMOVED: Charts functionality disabled"""
        pass

    def show_statistics_charts(self):
        """Display fancy histogram and pie charts for statistics visualization"""
        # DISABLED: This method is now replaced by integrated chart tabs
        print("show_statistics_charts called but disabled - using integrated tabs instead")
        return
        
        if not HAS_MATPLOTLIB:
            messagebox.showwarning("Charts Unavailable", 
                                 "Chart functionality is not available.\n"
                                 "Matplotlib is required for charts but not installed.\n"
                                 "The main application works without charts.")
            return
            
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            messagebox.showwarning("No Data", "Please select a folder with images first.")
            return
        
        # Create a new window for charts
        charts_window = tk.Toplevel(self.root)
        charts_window.title(f"Statistics Charts - Image Label Tool v{VERSION}")
        charts_window.geometry("1200x800")
        charts_window.configure(bg="#FAFAFA")
        
        # Create notebook for multiple chart tabs
        from tkinter import ttk
        notebook = ttk.Notebook(charts_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Image Classification Histogram
        hist_frame = ttk.Frame(notebook)
        notebook.add(hist_frame, text="Image Distribution")
        self.create_image_histogram(hist_frame)
        
        # Tab 2: Parcel Classification Pie Chart
        pie_frame = ttk.Frame(notebook)
        notebook.add(pie_frame, text="Parcel Breakdown")
        self.create_parcel_pie_chart(pie_frame)
        
        # Tab 3: Progress and Stats Overview
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="Progress Overview")
        self.create_progress_overview(overview_frame)
        
        # Center the window
        charts_window.transient(self.root)
        charts_window.grab_set()

    def _resize_existing_charts(self):
        """Resize existing matplotlib figures to fit current frame dimensions"""
        try:
            # Resize histogram chart
            if (hasattr(self, 'histogram_figure') and self.histogram_figure and 
                hasattr(self, 'histogram_canvas') and self.histogram_canvas and
                hasattr(self, 'charts_scrollable_frame')):
                
                # Check if the canvas widget still exists
                try:
                    canvas_widget = self.histogram_canvas.get_tk_widget()
                    if canvas_widget.winfo_exists():
                        # Get new dimensions for histogram
                        self.charts_scrollable_frame.update_idletasks()
                        frame_width = self.charts_scrollable_frame.winfo_width()
                        frame_height = self.charts_scrollable_frame.winfo_height()
                        
                        if frame_width > 1 and frame_height > 1:
                            fig_width = max(4, (frame_width - 80) / 100)
                            fig_height = max(3, (frame_height - 100) / 100)
                            fig_width = min(fig_width, 15)
                            fig_height = min(fig_height, 10)
                            
                            print(f"Resizing histogram to {fig_width:.1f}x{fig_height:.1f}")
                            self.histogram_figure.set_size_inches(fig_width, fig_height)
                            self.histogram_canvas.draw()
                    else:
                        print("Histogram canvas widget no longer exists, resetting references")
                        self.histogram_figure = None
                        self.histogram_canvas = None
                except tk.TclError:
                    print("Histogram canvas widget destroyed, resetting references")
                    self.histogram_figure = None
                    self.histogram_canvas = None
            
            # Resize pie chart
            if (hasattr(self, 'pie_figure') and self.pie_figure and 
                hasattr(self, 'pie_canvas') and self.pie_canvas and
                hasattr(self, 'parcel_charts_scrollable_frame')):
                
                # Check if the canvas widget still exists
                try:
                    canvas_widget = self.pie_canvas.get_tk_widget()
                    if canvas_widget.winfo_exists():
                        # Get new dimensions for pie chart
                        self.parcel_charts_scrollable_frame.update_idletasks()
                        frame_width = self.parcel_charts_scrollable_frame.winfo_width()
                        frame_height = self.parcel_charts_scrollable_frame.winfo_height()
                        
                        if frame_width > 1 and frame_height > 1:
                            fig_width = max(4, (frame_width - 80) / 100)
                            fig_height = max(6, (frame_height - 120) / 100)
                            fig_width = min(fig_width, 15)
                            fig_height = min(fig_height, 12)
                            
                            print(f"Resizing pie chart to {fig_width:.1f}x{fig_height:.1f}")
                            self.pie_figure.set_size_inches(fig_width, fig_height)
                            self.pie_canvas.draw()
                    else:
                        print("Pie canvas widget no longer exists, resetting references")
                        self.pie_figure = None
                        self.pie_canvas = None
                except tk.TclError:
                    print("Pie canvas widget destroyed, resetting references")
                    self.pie_figure = None
                    self.pie_canvas = None
                    
        except Exception as e:
            print(f"Error resizing charts: {e}")

    def _get_chart_data_hash(self):
        """Generate a hash of current chart data to detect changes"""
        try:
            # Collect current data
            image_counts = {label: 0 for label in LABELS}
            if hasattr(self, 'all_image_paths') and self.all_image_paths:
                for path in self.all_image_paths:
                    if path in self.labels and self.labels[path] != "(Unclassified)":
                        label = self.labels[path]
                        if label in image_counts:
                            image_counts[label] += 1
                    else:
                        image_counts["(Unclassified)"] += 1
            
            # Create simple hash of the data
            data_str = str(sorted(image_counts.items()))
            return hash(data_str)
        except:
            return None

    def _clear_chart_references(self):
        """Clear all chart references and close matplotlib figures"""
        try:
            if hasattr(self, 'histogram_figure') and self.histogram_figure:
                print(f"Closing histogram figure: {self.histogram_figure}")
                plt.close(self.histogram_figure)
            if hasattr(self, 'pie_figure') and self.pie_figure:
                print(f"Closing pie figure: {self.pie_figure}")
                plt.close(self.pie_figure)
        except Exception as e:
            print(f"Error closing figures: {e}")
        
        # Also close any orphaned figures
        try:
            plt.close('all')  # Close all matplotlib figures
            print("Closed all matplotlib figures")
        except Exception as e:
            print(f"Error closing all figures: {e}")
        
        self.histogram_figure = None
        self.histogram_canvas = None
        self.pie_figure = None
        self.pie_canvas = None
        print("Reset all chart references to None")

    def force_chart_resize(self):
        """Force resize of charts (called by button)"""
        print("Forcing chart resize...")
        if (hasattr(self, 'histogram_figure') and self.histogram_figure and 
            hasattr(self, 'pie_figure') and self.pie_figure):
            self._resize_existing_charts()
        else:
            # If charts don't exist, create them
            self.update_chart_tabs()

    def create_image_histogram(self, parent_frame):
        """Create a fancy histogram showing image classification distribution"""
        # Set up matplotlib style
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            plt.style.use('default')
        
        # Calculate image counts
        image_counts = {label: 0 for label in LABELS}
        if hasattr(self, 'all_image_paths') and self.all_image_paths:
            for path in self.all_image_paths:
                if path in self.labels and self.labels[path] != "(Unclassified)":
                    label = self.labels[path]
                    if label in image_counts:
                        image_counts[label] += 1
                else:
                    image_counts["(Unclassified)"] += 1
        
        # Prepare data for plotting
        labels = list(image_counts.keys())
        counts = list(image_counts.values())
        
        # Define attractive colors for each category
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
        
        # Calculate optimal figure size based on parent frame dimensions
        parent_frame.update_idletasks()  # Ensure geometry is calculated
        
        # Force multiple updates to ensure proper sizing
        for _ in range(3):
            parent_frame.update()
            parent_frame.update_idletasks()
        
        # Get frame dimensions with multiple attempts if needed
        frame_width = parent_frame.winfo_width()
        frame_height = parent_frame.winfo_height()
        print(f"Frame dimensions after updates: {frame_width}x{frame_height}")
        
        # If dimensions are still not valid, wait a bit and try again
        if frame_width <= 1 or frame_height <= 1:
            print("Dimensions still invalid, waiting and retrying...")
            parent_frame.after(100, lambda: parent_frame.update())
            parent_frame.update()
            frame_width = parent_frame.winfo_width()
            frame_height = parent_frame.winfo_height()
            print(f"Frame dimensions after wait: {frame_width}x{frame_height}")
        
        # Convert pixels to inches (assuming 100 DPI) with some padding
        if frame_width > 50 and frame_height > 50:  # Need reasonable minimum
            fig_width = max(4, (frame_width - 80) / 100)  # Min 4 inches, more padding
            fig_height = max(3, (frame_height - 100) / 100)  # Min 3 inches, more padding
            print(f"Calculated figure size: {fig_width:.1f}x{fig_height:.1f} inches")
        else:
            # Fallback dimensions if frame still not properly sized
            fig_width, fig_height = 6, 4
            print(f"Warning: Using fallback dimensions for chart. Frame size: {frame_width}x{frame_height}")
        
        # Ensure reasonable size limits
        fig_width = min(fig_width, 15)  # Max 15 inches wide
        fig_height = min(fig_height, 10)  # Max 10 inches tall
        
        # Create the figure and axis - responsive size with unique identifier
        import time
        fig_id = f"histogram_{int(time.time() * 1000)}"  # Unique ID based on timestamp
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), num=fig_id)
        
        # Create bars with custom styling
        bars = ax.bar(range(len(labels)), counts, color=colors[:len(labels)], 
                     alpha=0.8, edgecolor='white', linewidth=1)
        
        # Customize the plot with responsive font sizes
        title_size = max(10, min(14, fig_width * 2))
        label_size = max(8, min(12, fig_width * 1.5))
        tick_size = max(7, min(10, fig_width * 1.2))
        
        ax.set_title('Image Classification Distribution', fontsize=title_size, fontweight='bold', pad=15)
        ax.set_xlabel('Classification Labels', fontsize=label_size, fontweight='bold')
        ax.set_ylabel('Number of Images', fontsize=label_size, fontweight='bold')
        
        # Set x-axis labels with rotation
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=tick_size)
        
        # Add value labels on top of bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                       str(count), ha='center', va='bottom', fontweight='bold', fontsize=tick_size)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Improve layout
        plt.tight_layout()
        
        # Clear any existing widgets in the parent frame before adding new canvas
        print(f"Clearing {len(parent_frame.winfo_children())} existing widgets from histogram frame")
        for widget in list(parent_frame.winfo_children()):
            try:
                print(f"  Destroying histogram widget: {widget}")
                widget.destroy()
            except Exception as e:
                print(f"  Error destroying histogram widget: {e}")
        
        # Force update to ensure widgets are really gone
        parent_frame.update()
        
        # Embed the plot in tkinter and store references
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Store references for dynamic resizing
        self.histogram_figure = fig
        self.histogram_canvas = canvas
        print(f"Histogram canvas created with ID: {canvas}")  # Debug

    def create_parcel_pie_chart(self, parent_frame):
        """Create a fancy pie chart showing parcel classification distribution"""
        # Set up matplotlib style
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except:
            plt.style.use('default')
        
        # Calculate parcel statistics
        parcel_labels_dict = self.calculate_parcel_labels()
        
        if not parcel_labels_dict:
            # Show message if no parcel data
            label = tk.Label(parent_frame, text="📦 No parcel data available\nPlease classify some images first.",
                           font=("Arial", 14), bg="#FAFAFA", fg="#666666")
            label.pack(expand=True)
            return
        
        # Count parcels by label
        parcel_counts = {}
        for parcel_label in parcel_labels_dict.values():
            parcel_counts[parcel_label] = parcel_counts.get(parcel_label, 0) + 1
        
        # Prepare data for pie chart
        labels = list(parcel_counts.keys())
        sizes = list(parcel_counts.values())
        
        # Define attractive colors
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
        
        # Calculate optimal figure size based on parent frame dimensions
        parent_frame.update_idletasks()  # Ensure geometry is calculated
        
        # Force multiple updates to ensure proper sizing
        for _ in range(3):
            parent_frame.update()
            parent_frame.update_idletasks()
        
        # Get frame dimensions with multiple attempts if needed
        frame_width = parent_frame.winfo_width()
        frame_height = parent_frame.winfo_height()
        print(f"Pie chart frame dimensions after updates: {frame_width}x{frame_height}")
        
        # If dimensions are still not valid, wait a bit and try again
        if frame_width <= 1 or frame_height <= 1:
            print("Pie chart dimensions still invalid, waiting and retrying...")
            parent_frame.after(100, lambda: parent_frame.update())
            parent_frame.update()
            frame_width = parent_frame.winfo_width()
            frame_height = parent_frame.winfo_height()
            print(f"Pie chart frame dimensions after wait: {frame_width}x{frame_height}")
        
        # Convert pixels to inches (assuming 100 DPI) with some padding
        if frame_width > 50 and frame_height > 50:  # Need reasonable minimum
            fig_width = max(4, (frame_width - 80) / 100)  # Min 4 inches, more padding
            fig_height = max(6, (frame_height - 120) / 100)  # Min 6 inches for vertical layout
            print(f"Calculated pie chart figure size: {fig_width:.1f}x{fig_height:.1f} inches")
        else:
            # Fallback dimensions if frame still not properly sized
            fig_width, fig_height = 6, 8
            print(f"Warning: Using fallback dimensions for parcel chart. Frame size: {frame_width}x{frame_height}")
        
        # Ensure reasonable size limits
        fig_width = min(fig_width, 15)  # Max 15 inches wide
        fig_height = min(fig_height, 12)  # Max 12 inches tall
        
        # Create the figure with vertical layout - pie chart above, table below
        fig_id = f"pie_chart_{int(time.time() * 1000)}"  # Unique ID based on timestamp
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(fig_width, fig_height), 
                                      gridspec_kw={'height_ratios': [2, 1]}, num=fig_id)
        
        # Calculate responsive font sizes
        title_size = max(10, min(14, fig_width * 2))
        pie_label_size = max(8, min(11, fig_width * 1.5))
        pie_text_size = max(7, min(9, fig_width * 1.3))
        
        # Create pie chart
        wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors[:len(labels)],
                                          autopct='%1.1f%%', startangle=90, 
                                          explode=[0.05] * len(labels),
                                          shadow=True, textprops={'fontsize': pie_label_size})
        
        # Beautify the pie chart
        ax1.set_title('Parcel Classification Breakdown', fontsize=title_size, fontweight='bold', pad=15)
        
        # Make percentage text bold with responsive sizing
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(pie_text_size)
        
        # Create a detailed breakdown table below the pie chart
        ax2.axis('tight')
        ax2.axis('off')
        
        # Prepare table data
        total_parcels = sum(sizes)
        table_data = []
        for label, count in zip(labels, sizes):
            percentage = (count / total_parcels) * 100 if total_parcels > 0 else 0
            table_data.append([label, str(count), f"{percentage:.1f}%"])
        
        table_data.append(['TOTAL', str(total_parcels), '100.0%'])
        
        # Create table
        table = ax2.table(cellText=table_data,
                         colLabels=['Classification', 'Count', 'Percentage'],
                         cellLoc='center',
                         loc='center',
                         colColours=['#E3F2FD', '#E3F2FD', '#E3F2FD'])
        
        table.auto_set_font_size(False)
        table_font_size = max(7, min(10, fig_width * 1.2))
        table.set_fontsize(table_font_size)
        table.scale(1, max(1.2, min(1.8, fig_height * 0.2)))
        
        # Style the table
        for i in range(len(table_data) + 1):
            for j in range(3):
                cell = table[(i, j)]
                if i == 0:  # Header row
                    cell.set_text_props(weight='bold')
                    cell.set_facecolor('#1976D2')
                    cell.set_text_props(color='white')
                elif i == len(table_data):  # Total row
                    cell.set_text_props(weight='bold')
                    cell.set_facecolor('#E8F5E8')
        
        table_title_size = max(9, min(12, fig_width * 1.8))
        ax2.set_title('Detailed Breakdown', fontsize=table_title_size, fontweight='bold')
        
        plt.tight_layout(pad=2.0)
        
        # Clear any existing widgets in the parent frame before adding new canvas
        print(f"Clearing {len(parent_frame.winfo_children())} existing widgets from pie chart frame")
        for widget in list(parent_frame.winfo_children()):
            try:
                print(f"  Destroying pie chart widget: {widget}")
                widget.destroy()
            except Exception as e:
                print(f"  Error destroying pie chart widget: {e}")
        
        # Force update to ensure widgets are really gone
        parent_frame.update()
        
        # Embed the plot in tkinter and store references
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Store references for dynamic resizing
        self.pie_figure = fig
        self.pie_canvas = canvas
        print(f"Pie chart canvas created with ID: {canvas}")  # Debug

    def create_progress_overview(self, parent_frame):
        """Create a comprehensive progress overview with multiple visualizations"""
        # Set up the figure with subplots
        fig = plt.figure(figsize=(12, 8))
        
        # Create a 2x2 grid for multiple charts
        ax1 = plt.subplot(2, 2, 1)  # Progress pie chart
        ax2 = plt.subplot(2, 2, 2)  # Read rate bars
        ax3 = plt.subplot(2, 1, 2)   # Combined overview bar chart
        
        # 1. Progress Pie Chart (Classified vs Unclassified)
        if hasattr(self, 'all_image_paths') and self.all_image_paths:
            total_images = len(self.all_image_paths)
            classified_images = len([path for path in self.all_image_paths 
                                   if path in self.labels and self.labels[path] != "(Unclassified)"])
            unclassified_images = total_images - classified_images
            
            progress_sizes = [classified_images, unclassified_images]
            progress_labels = [f'Classified\n({classified_images})', f'Unclassified\n({unclassified_images})']
            progress_colors = ['#4CAF50', '#FF5722']
            
            wedges, texts, autotexts = ax1.pie(progress_sizes, labels=progress_labels, 
                                              colors=progress_colors, autopct='%1.1f%%',
                                              startangle=90, explode=[0.05, 0.05],
                                              shadow=True)
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                
            ax1.set_title('Classification Progress', fontweight='bold', fontsize=12)
        
        # 2. Read Rate Bars (if total parcels is set)
        try:
            total_entered = int(self.total_parcels_var.get()) if self.total_parcels_var.get() else 0
            if total_entered > 0:
                parcel_labels_dict = self.calculate_parcel_labels()
                actual_parcels = len(parcel_labels_dict)
                
                parcels_no_code = sum(1 for label in parcel_labels_dict.values() if label == "no code")
                parcels_read_failure = sum(1 for label in parcel_labels_dict.values() if label == "read failure")
                
                total_readable = total_entered - actual_parcels + parcels_read_failure
                
                # Calculate rates
                gross_rate = ((total_entered - actual_parcels) / total_entered * 100) if total_entered > 0 else 0
                net_rate = ((total_readable - parcels_read_failure) / total_readable * 100) if total_readable > 0 else 0
                
                rates = [gross_rate, net_rate]
                rate_labels = ['Gross Read Rate', 'Net Read Rate']
                rate_colors = ['#2196F3', '#FF9800']
                
                bars = ax2.bar(rate_labels, rates, color=rate_colors, alpha=0.8, edgecolor='white', linewidth=2)
                ax2.set_ylim(0, 100)
                ax2.set_ylabel('Percentage (%)', fontweight='bold')
                ax2.set_title('Read Rates', fontweight='bold', fontsize=12)
                
                # Add percentage labels on bars
                for bar, rate in zip(bars, rates):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                           f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
            else:
                ax2.text(0.5, 0.5, '📝 Enter total parcels\nto see read rates', 
                        transform=ax2.transAxes, ha='center', va='center',
                        fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
                ax2.set_xticks([])
                ax2.set_yticks([])
        except Exception as e:
            ax2.text(0.5, 0.5, '❌ Read rate calculation\nunavailable', 
                    transform=ax2.transAxes, ha='center', va='center',
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.5))
        
        # 3. Combined Overview Bar Chart
        image_counts = {label: 0 for label in LABELS}
        if hasattr(self, 'all_image_paths') and self.all_image_paths:
            for path in self.all_image_paths:
                if path in self.labels and self.labels[path] != "(Unclassified)":
                    label = self.labels[path]
                    if label in image_counts:
                        image_counts[label] += 1
                else:
                    image_counts["(Unclassified)"] += 1
        
        # Filter out zero counts for cleaner display
        filtered_labels = []
        filtered_counts = []
        filtered_colors = []
        base_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
        
        for i, (label, count) in enumerate(image_counts.items()):
            if count > 0:
                filtered_labels.append(label)
                filtered_counts.append(count)
                filtered_colors.append(base_colors[i % len(base_colors)])
        
        if filtered_counts:
            bars = ax3.bar(range(len(filtered_labels)), filtered_counts, 
                          color=filtered_colors, alpha=0.8, edgecolor='white', linewidth=2)
            
            ax3.set_xticks(range(len(filtered_labels)))
            ax3.set_xticklabels(filtered_labels, rotation=45, ha='right')
            ax3.set_ylabel('Count', fontweight='bold')
            ax3.set_title('Complete Classification Overview', fontweight='bold', fontsize=14, pad=15)
            
            # Add count labels on bars
            for bar, count in zip(bars, filtered_counts):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(filtered_counts)*0.01,
                       str(count), ha='center', va='bottom', fontweight='bold')
            
            ax3.grid(True, alpha=0.3, axis='y')
            ax3.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Embed the plot in tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_counts(self):
        counts = {label: 0 for label in LABELS}
        
        # Count all images, including unclassified ones
        if hasattr(self, 'all_image_paths') and self.all_image_paths:
            for path in self.all_image_paths:
                if path in self.labels and self.labels[path] != "(Unclassified)":
                    # Image has a real classification
                    label = self.labels[path]
                    if label in counts:
                        counts[label] += 1
                else:
                    # Image is unclassified
                    counts["(Unclassified)"] += 1
        
        # Multi-line format for better readability
        lines = []
        for label in LABELS:
            lines.append(f"  {label}: {counts[label]}")
        self.count_var.set("\n".join(lines))
        
        # Charts removed - no longer updating charts
        
        # Update warning message
        self.update_warning_message()

    def update_progress_display(self):
        """Update the progress counter showing classified vs total images"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            self.progress_var.set("")
            return
        
        total_images = len(self.all_image_paths)
        classified_images = len([path for path in self.all_image_paths if path in self.labels and self.labels[path] != "(Unclassified)"])
        unclassified_images = total_images - classified_images
        
        # Multi-line format for better readability
        progress_text = f"{classified_images}/{total_images} classified\n({unclassified_images} remaining)"
        self.progress_var.set(progress_text)
        
        # Change text color based on remaining count (but keep consistent font size)
        if unclassified_images > 0:
            # Bold red text when there are remaining images
            self.progress_label.config(fg="red", font=("Arial", 13, "bold"))
        else:
            # Normal green text when all images are classified
            self.progress_label.config(fg="#2E7D32", font=("Arial", 13, "normal"))

    def update_current_label_status(self):
        """Update the current image label status indicator"""
        if not self.image_paths:
            self.label_status_var.set("")
            return
        
        current_path = self.image_paths[self.current_index]
        if current_path in self.labels and self.labels[current_path] != "(Unclassified)":
            # Image has been classified
            self.label_status_var.set("✓ CLASSIFIED")
            self.label_status_label.config(fg="#81C784")  # Soft green
        else:
            # Image is unclassified
            self.label_status_var.set("○ UNCLASSIFIED")
            self.label_status_label.config(fg="#EF9A9A")  # Soft red
    
    def update_parcel_index_display(self):
        """Update the parcel index display for current image."""
        if not self.image_paths:
            self.parcel_index_var.set("")
            return
        
        current_path = self.image_paths[self.current_index]
        parcel_index = self.get_parcel_index(current_path)
        
        if parcel_index is not None:
            self.parcel_index_var.set(f"Parcel Index: {parcel_index}")
        else:
            self.parcel_index_var.set("Parcel Index: None")

    def get_parcel_number(self, image_path):
        """Extract the group ID from filename using ID (first part) + Timestamp (last part)"""
        filename = os.path.basename(image_path)
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Split by underscore to get parts
        parts = filename_without_ext.split('_')
        if len(parts) >= 2:
            # Get ID (first part) and timestamp (last part)
            id_part = parts[0]
            timestamp_part = parts[-1]
            # Return concatenated ID + timestamp as unique group identifier
            group_id = f"{id_part}_{timestamp_part}"
            return group_id
        elif len(parts) == 1:
            # If only one part, use it as both ID and timestamp
            return parts[0]
        else:
            # If no underscore, use the entire filename as identifier
            return filename_without_ext

    def calculate_parcel_labels(self):
        """Calculate parcel labels based on the labeling rules and return a dict"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return {}

        # Group images by their unique identifier (ID + Timestamp combination)
        parcels = {}
        for path in self.all_image_paths:
            parcel_id = self.get_parcel_number(path)
            if parcel_id:
                if parcel_id not in parcels:
                    parcels[parcel_id] = []
                parcels[parcel_id].append(path)

        # Calculate parcel labels based on rules with new 7-category system
        parcel_labels_dict = {}
        
        for parcel_id, parcel_paths in parcels.items():
            parcel_image_labels = [self.labels.get(path, LABELS[0]) for path in parcel_paths]
            
            # Only include parcels that have at least one classified image
            classified_labels = [label for label in parcel_image_labels if label != "(Unclassified)"]
            
            if not classified_labels:
                # Skip parcels with no classified images
                continue
            
            # Apply parcel labeling rules in priority order:
            # 1. If any image has "read failure", parcel is "read failure" (technical issue)
            if "read failure" in classified_labels:
                parcel_labels_dict[parcel_id] = "read failure"
            # 2. If any image is "damaged", parcel is "damaged" (physical issue)
            elif "damaged" in classified_labels:
                parcel_labels_dict[parcel_id] = "damaged"
            # 3. If any image has "image quality" issues, parcel has "image quality" issues
            elif "image quality" in classified_labels:
                parcel_labels_dict[parcel_id] = "image quality"
            # 4. If any image is "occluded", parcel is "occluded"
            elif "occluded" in classified_labels:
                parcel_labels_dict[parcel_id] = "occluded"
            # 5. If any image is "other", parcel is "other"
            elif "other" in classified_labels:
                parcel_labels_dict[parcel_id] = "other"
            # 6. If ALL classified images are "no code", parcel is "no code"
            elif all(label == "no code" for label in classified_labels):
                parcel_labels_dict[parcel_id] = "no code"
            # 7. Default: if mix of categories, parcel is "other"
            else:
                parcel_labels_dict[parcel_id] = "other"
                
        return parcel_labels_dict

    def update_parcel_stats(self):
        """Calculate parcel statistics based on the labeling rules"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            self.parcel_count_var.set("")
            return

        parcel_labels_dict = self.calculate_parcel_labels()
        
        # Count parcels by different categories
        total_parcels = len(parcel_labels_dict)
        parcels_no_code = 0
        parcels_read_failure = 0
        
        for parcel_label in parcel_labels_dict.values():
            if parcel_label == "no code":
                parcels_no_code += 1
            elif parcel_label == "read failure":
                parcels_read_failure += 1
        
        # Calculate total readable parcels using expected total from text field
        try:
            total_entered = int(self.total_parcels_var.get()) if self.total_parcels_var.get() else 0
            # Total readable = Total number of parcel - number of parcels + Parcels with read failure
            total_readable = total_entered - total_parcels + parcels_read_failure
        except ValueError:
            total_readable = "N/A (Enter expected total)"
        
        # Format the display
        lines = [
            f"Number of parcels: {total_parcels}",
            f"Parcels with no code: {parcels_no_code}",
            f"Parcels with read failure: {parcels_read_failure}",
            f"Total readable parcels: {total_readable}"
        ]
        
        self.parcel_count_var.set("\n".join(lines))

    def update_total_stats(self):
        """Calculate statistics against manually entered total number of parcels"""
        try:
            total_entered = int(self.total_parcels_var.get()) if self.total_parcels_var.get() else 0
        except ValueError:
            self.parcel_stats_var.set("")
            return

        if total_entered <= 0:
            self.parcel_stats_var.set("")
            return

        # Get current parcel statistics
        parcel_labels_dict = self.calculate_parcel_labels()
        actual_parcels = len(parcel_labels_dict)
        
        parcels_no_code = 0
        parcels_read_failure = 0
        
        for parcel_label in parcel_labels_dict.values():
            if parcel_label == "no code":
                parcels_no_code += 1
            elif parcel_label == "read failure":
                parcels_read_failure += 1
        
        # Calculate readable parcels: Total number of parcel - number of parcels + Parcels with read failure
        total_readable = total_entered - actual_parcels + parcels_read_failure
        
        lines = []
        
        # Gross read rate: (Total number of parcels) minus (Number of parcels) out of (Total number of parcels)
        if total_entered > 0:
            gross_numerator = total_entered - actual_parcels
            gross_read_rate = (gross_numerator / total_entered) * 100
            lines.append(f"Gross read rate: {gross_numerator}/{total_entered} ({gross_read_rate:.1f}%)")
        
        # Net read rate: (Total number of readable parcels) minus (Parcels with read failure) out of (Total number of readable parcels)
        if total_readable > 0:
            net_numerator = total_readable - parcels_read_failure
            net_read_rate = (net_numerator / total_readable) * 100
            lines.append(f"Net read rate: {net_numerator}/{total_readable} ({net_read_rate:.1f}%)")
        
        self.parcel_stats_var.set("\n".join(lines))

    def auto_detect_total_groups(self):
        """Auto-detect total number of parcels by finding the highest ID value from filenames"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return
        
        max_id = 0
        for path in self.all_image_paths:
            filename = os.path.basename(path)
            filename_without_ext = os.path.splitext(filename)[0]
            
            # Split by underscore to get parts
            parts = filename_without_ext.split('_')
            if len(parts) >= 1:
                try:
                    # Get ID (first part before first underscore) and convert to number
                    id_part = parts[0]
                    id_number = int(id_part)
                    max_id = max(max_id, id_number)
                except ValueError:
                    # Skip files where the first part is not a number
                    continue
        
        if max_id > 0:
            # Set the total parcels field with the highest ID value found
            self.total_parcels_var.set(str(max_id))
            # Update statistics immediately
            self.update_total_stats()

    def on_window_resize(self, event):
        """Handle window resize events to update image display"""
        # Only respond to resize events from the main window
        if event.widget == self.root:
            # Update image display if images are loaded
            if hasattr(self, 'image_paths') and self.image_paths:
                # Use after_idle to ensure the window has finished resizing
                self.root.after_idle(self.show_image)

    def _delayed_chart_update(self):
        """REMOVED: Charts functionality disabled"""
        pass

    def update_chart_tabs(self):
        """REMOVED: Charts functionality disabled"""
        pass

    def _resize_existing_charts(self):
        """REMOVED: Charts functionality disabled"""
        pass

    def _get_chart_data_hash(self):
        """REMOVED: Charts functionality disabled"""
        return None

    def _clear_chart_references(self):
        """REMOVED: Charts functionality disabled"""
        pass

    def force_chart_resize(self):
        """REMOVED: Charts functionality disabled"""
        pass

    def create_image_histogram(self, parent_frame):
        """REMOVED: Charts functionality disabled"""
        label = tk.Label(parent_frame, text="📊 Charts have been disabled\nfor better stability",
                       font=("Arial", 14), bg="#FAFAFA", fg="#666666")
        label.pack(expand=True)

    def create_parcel_pie_chart(self, parent_frame):
        """REMOVED: Charts functionality disabled"""
        label = tk.Label(parent_frame, text="📊 Charts have been disabled\nfor better stability",
                       font=("Arial", 14), bg="#FAFAFA", fg="#666666")
        label.pack(expand=True)

    def toggle_1to1_scale(self):
        """Toggle between fitted view and 1:1 scale view"""
        self.scale_1to1 = not self.scale_1to1
        
        if self.scale_1to1:
            self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
            self.zoom_level = 1.0  # Reset zoom level when entering 1:1 mode
        else:
            self.btn_1to1.config(text="1:1 Scale", bg="#FFCC80")
        
        # Refresh the current image display
        if hasattr(self, 'image_paths') and self.image_paths:
            self.show_image()

    def reset_to_fit_mode(self):
        """Reset image display to fit mode (scale to fit window)"""
        self.scale_1to1 = False
        self.zoom_level = 1.0
        self.btn_1to1.config(text="1:1 Scale", bg="#FFCC80")

    def zoom_in(self):
        """Increase zoom level"""
        if self.scale_1to1:
            # Already in 1:1 mode, increment zoom level
            self.zoom_level = min(self.zoom_level * 1.25, 5.0)  # Max 500% zoom
        else:
            # Switch to 1:1 mode and start from current scale factor
            self.scale_1to1 = True
            self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
            # Start zoom from current fitted scale and increment it
            current_scale = getattr(self, 'current_scale_factor', 1.0)
            self.zoom_level = min(current_scale * 1.25, 5.0)  # Increment from current scale
        self.show_image()

    def zoom_out(self):
        """Decrease zoom level"""
        if self.scale_1to1:
            # Already in 1:1 mode, decrement zoom level
            self.zoom_level = max(self.zoom_level / 1.25, 0.1)  # Min 10% zoom
        else:
            # Switch to 1:1 mode and start from current scale factor
            self.scale_1to1 = True
            self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
            # Start zoom from current fitted scale and decrement it
            current_scale = getattr(self, 'current_scale_factor', 1.0)
            self.zoom_level = max(current_scale / 1.25, 0.1)  # Decrement from current scale
        self.show_image()

    def mouse_wheel_zoom(self, event):
        """Handle mouse wheel zoom"""
        # Allow mouse wheel zoom in both fit and 1:1 modes
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def start_pan(self, event):
        """Start panning with mouse"""
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        """Perform panning with mouse drag"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def detect_barcode_count(self, image_path):
        """Detect barcode in an image and return the count of detected barcodes"""
        try:
            # Log the start of detection
            filename = os.path.basename(image_path)
            self.logger.info(f"Starting barcode detection for: {filename}")
            
            # Read the image using OpenCV
            image = cv2.imread(image_path)
            if image is None:
                self.logger.warning(f"Could not read image: {filename}")
                return 0
            
            # Log image properties
            height, width = image.shape[:2]
            self.logger.info(f"Image dimensions: {width}x{height} pixels")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Look for barcode-like rectangular patterns
            barcode_count_method1 = self._detect_barcode_patterns(gray)
            self.logger.info(f"Method 1 (Pattern Detection) found: {barcode_count_method1} barcodes")
            
            # Method 2: If no patterns found, use gradient-based detection
            barcode_count_method2 = 0
            if barcode_count_method1 == 0:
                barcode_count_method2 = self._detect_barcode_gradients(gray)
                self.logger.info(f"Method 2 (Gradient Detection) found: {barcode_count_method2} barcodes")
            
            final_count = max(barcode_count_method1, barcode_count_method2)
            
            # Log the final result
            if final_count > 0:
                self.logger.info(f"✓ DETECTION SUCCESS: {final_count} barcode(s) detected in {filename}")
            else:
                self.logger.info(f"○ NO BARCODES: No barcodes detected in {filename}")
            
            return final_count
            
        except Exception as e:
            # Log the error
            self.logger.error(f"ERROR detecting barcode in {os.path.basename(image_path)}: {str(e)}")
            return 0
    
    def _detect_barcode_patterns(self, gray):
        """Detect barcodes using contour analysis"""
        self.logger.debug("Using pattern detection method (morphological operations)")
        
        # Apply morphological operations to enhance barcode patterns
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        morphed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Apply threshold
        _, binary = cv2.threshold(morphed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.logger.debug(f"Found {len(contours)} contours in pattern detection")
        
        barcode_count = 0
        
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            area = cv2.contourArea(contour)
            
            # Barcode characteristics: wide, not too tall, reasonable size
            if (area > 500 and 
                aspect_ratio > 2.5 and 
                aspect_ratio < 15 and
                w > 40 and h > 8):
                barcode_count += 1
                self.logger.debug(f"Pattern {i}: BARCODE CANDIDATE - area={area:.0f}, ratio={aspect_ratio:.2f}, size={w}x{h}")
            else:
                self.logger.debug(f"Pattern {i}: rejected - area={area:.0f}, ratio={aspect_ratio:.2f}, size={w}x{h}")
        
        return barcode_count
    
    def _detect_barcode_gradients(self, gray):
        """Detect barcodes using gradient analysis"""
        self.logger.debug("Using gradient detection method (edge analysis)")
        
        # Calculate gradient
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        
        # Calculate gradient magnitude and direction
        magnitude = cv2.magnitude(grad_x, grad_y)
        
        # Apply threshold to get strong edges
        _, edges = cv2.threshold(magnitude, 50, 255, cv2.THRESH_BINARY)
        edges = edges.astype(np.uint8)
        
        # Morphological operations to connect barcode lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3))
        morphed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.logger.debug(f"Found {len(contours)} contours in gradient detection")
        
        barcode_count = 0
        
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            area = cv2.contourArea(contour)
            
            # Look for horizontal patterns typical of barcodes
            if (area > 200 and 
                aspect_ratio > 1.5 and 
                aspect_ratio < 20 and
                w > 30):
                
                # Additional check: analyze the region for barcode-like patterns
                roi = gray[y:y+h, x:x+w]
                if roi.size > 0 and self._has_barcode_pattern(roi):
                    barcode_count += 1
                    self.logger.debug(f"Gradient {i}: BARCODE CANDIDATE - area={area:.0f}, ratio={aspect_ratio:.2f}, size={w}x{h}")
                else:
                    self.logger.debug(f"Gradient {i}: failed pattern test - area={area:.0f}, ratio={aspect_ratio:.2f}, size={w}x{h}")
            else:
                self.logger.debug(f"Gradient {i}: rejected - area={area:.0f}, ratio={aspect_ratio:.2f}, size={w}x{h}")
        
        return barcode_count
    
    def _has_barcode_pattern(self, roi):
        """Check if a region has barcode-like vertical line patterns"""
        if roi.shape[1] < 10:  # Too narrow
            self.logger.debug("ROI too narrow for barcode pattern analysis")
            return False
        
        # Calculate vertical profile (sum along columns)
        vertical_profile = np.mean(roi, axis=0)
        
        # Count transitions from dark to light and vice versa
        threshold = np.mean(vertical_profile)
        binary_profile = vertical_profile > threshold
        
        transitions = 0
        for i in range(1, len(binary_profile)):
            if binary_profile[i] != binary_profile[i-1]:
                transitions += 1
        
        # Barcodes should have many transitions (typically >6 for even simple codes)
        has_pattern = transitions > 6
        self.logger.debug(f"Pattern analysis: {transitions} transitions, {'PASS' if has_pattern else 'FAIL'}")
        return has_pattern

    def auto_detect_function(self, image_path):
        """Auto-detect function that detects barcodes in an image"""
        return self.detect_barcode_count(image_path)

    def check_for_new_files(self):
        """Check for new image files in the folder that weren't seen before"""
        if not hasattr(self, 'folder_path') or not self.folder_path:
            return []
        
        # Scan current folder for all image files
        try:
            all_files = [f for f in os.listdir(self.folder_path)
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
            
            current_image_paths = []
            for f in all_files:
                current_image_paths.append(os.path.join(self.folder_path, f))
            
            current_image_paths_set = set(current_image_paths)
            
            # Find new files (not in previously seen files)
            new_files = current_image_paths_set - self.previously_seen_files
            
            # Update our records
            if new_files:
                self.previously_seen_files.update(new_files)
                # Also update all_image_paths to include new files
                self.all_image_paths = sorted(current_image_paths)
                # Refresh the display if needed
                self.apply_filter()
            
            return list(new_files)
            
        except OSError as e:
            self.logger.error(f"Error scanning folder for new files: {e}")
            return []

    def get_new_unlabeled_files(self):
        """Get list of newly added files that are unlabeled"""
        new_files = self.check_for_new_files()
        
        # Filter to only unlabeled files
        new_unlabeled = []
        for file_path in new_files:
            if file_path not in self.labels or self.labels[file_path] == "(Unclassified)":
                new_unlabeled.append(file_path)
        
        return new_unlabeled

    def get_unclassified_images(self):
        """Get list of images that are not yet in the CSV (unclassified)"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return []
        
        # Load existing labels from CSV
        existing_labels = set()
        if hasattr(self, 'labels') and self.labels:
            existing_labels = set(self.labels.keys())
        
        # Find unclassified images
        unclassified = []
        for path in self.all_image_paths:
            if path not in existing_labels:
                unclassified.append(path)
        
        return unclassified

    def auto_code_detection(self):
        """Main auto code classification method that processes unclassified images"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            messagebox.showwarning("No Images", "Please select a folder with images first.")
            return
        
        unclassified_images = self.get_unclassified_images()
        
        # Log the start of auto-classification
        self.logger.info("-" * 50)
        self.logger.info("AUTO-CLASSIFICATION SESSION STARTED")
        self.logger.info(f"Total images in folder: {len(self.all_image_paths)}")
        self.logger.info(f"Unclassified images to process: {len(unclassified_images)}")
        
        if not unclassified_images:
            self.logger.info("All images are already classified!")
            messagebox.showinfo("Complete", "All images are already classified!")
            return
        
        # Disable all UI controls during processing (no button to disable)
        self.disable_ui_controls()
        
        # Start processing in a separate thread to avoid freezing the UI
        processing_thread = threading.Thread(target=self.process_auto_detection, args=(unclassified_images,))
        processing_thread.daemon = True
        processing_thread.start()

    def process_auto_detection(self, unclassified_images):
        """Process auto classification for unclassified images in a separate thread"""
        total_images = len(unclassified_images)
        processed = 0
        no_code_count = 0
        read_failure_count = 0
        
        self.logger.info(f"Processing {total_images} unclassified images...")
        
        for image_path in unclassified_images:
            # Update progress on UI thread
            self.root.after(0, self.update_auto_detect_progress, processed, total_images, os.path.basename(image_path))
            
            # Get auto detection result
            detection_result = self.auto_detect_function(image_path)
            
            # Determine label based on result with new 7-category system
            if detection_result == 0:
                label = "no code"  # No barcode detected
                no_code_count += 1
            else:  # detection_result > 0
                label = "read failure"  # Barcode detected but not readable
                read_failure_count += 1
            
            # Log the classification decision
            filename = os.path.basename(image_path)
            self.logger.info(f"CLASSIFIED: {filename} → {label} (barcode count: {detection_result})")
            
            # Update labels dictionary
            if not hasattr(self, 'labels'):
                self.labels = {}
            self.labels[image_path] = label
            
            # If this is the currently displayed image, refresh the display immediately
            if (hasattr(self, 'image_paths') and self.image_paths and 
                self.current_index < len(self.image_paths) and 
                image_path == self.image_paths[self.current_index]):
                self.root.after(0, self.show_image)
            
            # Save to CSV immediately
            self.root.after(0, self.save_csv)
            
            # Update statistics
            self.root.after(0, self.update_total_stats)
            self.root.after(0, self.update_parcel_stats)
            
            # Small delay to show progress (and simulate processing time)
            time.sleep(0.1)
            
            processed += 1
        
        # Log session summary
        self.logger.info("-" * 30)
        self.logger.info("AUTO-CLASSIFICATION SUMMARY:")
        self.logger.info(f"Total processed: {total_images}")
        self.logger.info(f"Classified as 'no code': {no_code_count}")
        self.logger.info(f"Classified as 'read failure': {read_failure_count}")
        self.logger.info("AUTO-CLASSIFICATION SESSION COMPLETED")
        self.logger.info("-" * 50)
        
        # Final update
        self.root.after(0, self.complete_auto_detection, total_images)

    def update_auto_detect_progress(self, processed, total, current_file):
        """Update the progress display for auto detection"""
        progress_text = f"Processing: {processed}/{total}\nCurrent: {current_file}"
        self.auto_detect_progress_var.set(progress_text)

    def complete_auto_detection(self, total_processed):
        """Complete the auto classification process"""
        # Re-enable all UI controls (no button to re-enable)
        self.enable_ui_controls()
        
        # Update progress display
        self.auto_detect_progress_var.set(f"Completed!\nProcessed {total_processed} images")
        
        # Save CSV and stats after bulk classification changes
        self.save_csv()
        
        # Update all statistics panels
        self.update_progress_display()
        self.update_counts()
        self.update_total_stats()
        self.update_parcel_stats()
        
        # Refresh the current image display to update radio button and status
        if hasattr(self, 'image_paths') and self.image_paths and self.current_index < len(self.image_paths):
            self.show_image()

    def process_auto_detection_on_new_files(self, new_files):
        """Process auto detection specifically for new files in a separate thread"""
        processing_thread = threading.Thread(target=self.run_auto_detection_on_new_files, args=(new_files,))
        processing_thread.daemon = True
        processing_thread.start()

    def run_auto_detection_on_new_files(self, new_files):
        """Run auto detection on new files only"""
        total_files = len(new_files)
        processed = 0
        no_code_count = 0
        read_failure_count = 0
        
        self.logger.info(f"Processing {total_files} new unlabeled files...")
        
        for file_path in new_files:
            # Update progress on UI thread
            filename = os.path.basename(file_path)
            self.root.after(0, self.update_auto_detect_progress, processed, total_files, filename)
            
            # Get auto detection result
            detection_result = self.auto_detect_function(file_path)
            
            # Determine label based on result
            if detection_result == 0:
                label = "no code"  # No barcode detected
                no_code_count += 1
            else:  # detection_result > 0
                label = "read failure"  # Barcode detected but not readable
                read_failure_count += 1
            
            # Log the classification decision
            self.logger.info(f"NEW FILE CLASSIFIED: {filename} → {label} (barcode count: {detection_result})")
            
            # Update labels dictionary
            if not hasattr(self, 'labels'):
                self.labels = {}
            self.labels[file_path] = label
            
            # Save to CSV and update stats
            self.root.after(0, self.save_csv)
            self.root.after(0, self.update_counts)
            self.root.after(0, self.update_total_stats)
            self.root.after(0, self.update_parcel_stats)
            
            # Small delay to show progress
            time.sleep(0.1)
            processed += 1
        
        # Log session summary
        self.logger.info("-" * 30)
        self.logger.info("NEW FILES AUTO-CLASSIFICATION SUMMARY:")
        self.logger.info(f"Total new files processed: {total_files}")
        self.logger.info(f"Classified as 'no code': {no_code_count}")
        self.logger.info(f"Classified as 'read failure': {read_failure_count}")
        self.logger.info("NEW FILES AUTO-CLASSIFICATION COMPLETED")
        self.logger.info("-" * 30)
        
        # Final update
        self.root.after(0, self.complete_new_files_detection, total_files)

    def complete_new_files_detection(self, total_processed):
        """Complete the new files auto classification process"""
        # Update progress display
        self.auto_detect_progress_var.set(f"Completed processing {total_processed} new files!")
        
        # Refresh the current image display
        if hasattr(self, 'image_paths') and self.image_paths and self.current_index < len(self.image_paths):
            self.show_image()

    def toggle_auto_timer(self):
        """Toggle the auto-timer functionality"""
        if not self.auto_timer_enabled.get():
            # Starting the timer
            self.start_auto_timer()
        else:
            # Stopping the timer
            self.stop_auto_timer()

    def generate_filter_folder(self):
        """Generate a timestamped folder and copy all images matching current filter into it"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            messagebox.showwarning("No Images", "Please select a folder with images first.")
            return
        
        filter_value = self.filter_var.get()
        
        # Skip for disabled filters
        if filter_value in ["All images", "(Unclassified) only"]:
            messagebox.showinfo("Invalid Filter", "This function is not available for 'All images' or 'Unclassified' filters.")
            return
        
        # Map filter names to label values and folder names
        filter_map = {
            "no code only": ("no code", "no_code"),
            "read failure only": ("read failure", "read_failure"),
            "occluded only": ("occluded", "occluded"),
            "image quality only": ("image quality", "image_quality"),
            "damaged only": ("damaged", "damaged"),
            "other only": ("other", "other")
        }
        
        if filter_value not in filter_map:
            messagebox.showerror("Invalid Filter", f"Unknown filter: {filter_value}")
            return
        
        label_value, folder_prefix = filter_map[filter_value]
        
        # Find all images matching the current filter
        matching_images = [path for path in self.all_image_paths 
                          if path in self.labels and self.labels[path] == label_value]
        
        if not matching_images:
            messagebox.showinfo("No Images", f"No '{label_value}' images found to copy.")
            return
        
        # Disable button during processing
        self.btn_gen_filter_folder.config(state='disabled', text="Generating...")
        
        # Use the progress display for feedback
        self.auto_detect_progress_var.set(f"Preparing to copy {len(matching_images)} '{label_value}' images...")
        
        # Start processing in a separate thread to avoid freezing the UI
        import threading
        processing_thread = threading.Thread(target=self.process_filter_copy, args=(matching_images, label_value, folder_prefix))
        processing_thread.daemon = True
        processing_thread.start()

    def process_filter_copy(self, matching_images, label_value, folder_prefix):
        """Process copying filter images in a separate thread"""
        import shutil
        from datetime import datetime
        
        try:
            # Check if folder_path exists
            if not hasattr(self, 'folder_path') or not self.folder_path:
                raise Exception("No folder selected")
                
            # Create timestamped folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"{folder_prefix}_{timestamp}"
            destination_folder = os.path.join(self.folder_path, folder_name)
            
            # Create the directory
            os.makedirs(destination_folder, exist_ok=True)
            
            total_images = len(matching_images)
            copied = 0
            
            for image_path in matching_images:
                # Update progress on UI thread
                filename = os.path.basename(image_path)
                self.root.after(0, self.update_copy_progress, copied + 1, total_images, filename)
                
                # Copy the file
                destination_path = os.path.join(destination_folder, filename)
                shutil.copy2(image_path, destination_path)
                
                copied += 1
                
                # Small delay to show progress
                import time
                time.sleep(0.05)
            
            # Completion
            self.root.after(0, self.complete_filter_copy, total_images, folder_name, label_value)
            
        except Exception as e:
            # Error handling
            self.root.after(0, self.copy_error, str(e))

    def update_copy_progress(self, current, total, filename):
        """Update the progress display for copying"""
        progress_text = f"Copying {current}/{total}\n{filename}"
        self.auto_detect_progress_var.set(progress_text)

    def complete_filter_copy(self, total_copied, folder_name, label_value):
        """Complete the copy operation"""
        # Re-enable button with current filter state
        self.update_filter_button_state()
        self.btn_gen_filter_folder.config(text="Gen Filter Folder")
        
        # Show completion message
        self.auto_detect_progress_var.set(f"Completed!\nCopied {total_copied} images to:\n{folder_name}")
        
        # Show success dialog
        messagebox.showinfo("Copy Complete", 
                          f"Successfully copied {total_copied} '{label_value}' images to folder:\n{folder_name}")

    def copy_error(self, error_message):
        """Handle copy operation errors"""
        # Re-enable button with current filter state
        self.update_filter_button_state()
        self.btn_gen_filter_folder.config(text="Gen Filter Folder")
        
        # Show error message
        self.auto_detect_progress_var.set("Copy failed!")
        messagebox.showerror("Copy Error", f"Failed to copy images:\n{error_message}")

    def start_auto_timer(self):
        """Start the auto-timer for periodic auto detection"""
        try:
            interval_minutes = float(self.auto_timer_interval.get())
            if interval_minutes <= 0:
                raise ValueError("Interval must be positive")
        except ValueError:
            messagebox.showerror("Invalid Interval", "Please enter a valid positive number for minutes.")
            return
        
        self.stop_auto_timer()  # Stop any existing timer
        
        # Check for new images immediately when Start is clicked
        from datetime import datetime
        current_time = datetime.now().strftime('%H:%M:%S')
        self.auto_timer_status_var.set(f"[{current_time}] Checking for new unlabeled files...")
        
        new_unlabeled_files = self.get_new_unlabeled_files()
        
        if new_unlabeled_files:
            self.auto_timer_status_var.set(f"Found {len(new_unlabeled_files)} new unlabeled files!")
            
            # Log the discovery of new files
            self.logger.info(f"Start button: Found {len(new_unlabeled_files)} new unlabeled files")
            for file_path in new_unlabeled_files:
                self.logger.info(f"New file: {os.path.basename(file_path)}")
            
            # Check if auto-detection is enabled
            if self.auto_detect_enabled.get():
                self.auto_timer_status_var.set(f"Auto-detecting barcodes in {len(new_unlabeled_files)} new files...")
                # Run auto-detection on new files only
                self.process_auto_detection_on_new_files(new_unlabeled_files)
            else:
                self.auto_timer_status_var.set(f"Found {len(new_unlabeled_files)} new files - monitoring started")
                # Update the CSV to mark these as unclassified
                for file_path in new_unlabeled_files:
                    self.labels[file_path] = "(Unclassified)"
                self.save_csv()
                self.update_counts()
                # Refresh the UI to show the new images
                self.apply_filter()
        else:
            self.auto_timer_status_var.set(f"[{current_time}] No new unlabeled files found - monitoring started")
            self.logger.info("Start button: No new unlabeled files found")
        
        # Update UI state
        self.auto_timer_enabled.set(True)
        self.auto_timer_button.config(text="Stop", bg="#f44336", activebackground="#d32f2f")
        self.auto_timer_entry.config(state='disabled')
        
        # Disable only folder selection while monitoring (keep radio buttons and filter active)
        self.disable_ui_controls_for_monitoring()
        
        interval_ms = int(interval_minutes * 60 * 1000)  # Convert minutes to milliseconds
        self.auto_timer_job = self.root.after(interval_ms, self.run_auto_detection_timer)
        
        # Start countdown display
        self.start_countdown(interval_minutes)
        
    def stop_auto_timer(self):
        """Stop the auto-timer"""
        if self.auto_timer_job:
            self.root.after_cancel(self.auto_timer_job)
            self.auto_timer_job = None
        
        # Stop countdown
        self.stop_countdown()
        
        # Check for new images immediately when Stop is clicked
        if hasattr(self, 'auto_timer_enabled') and self.auto_timer_enabled.get():
            from datetime import datetime
            current_time = datetime.now().strftime('%H:%M:%S')
            self.auto_timer_status_var.set(f"[{current_time}] Final check for new unlabeled files...")
            
            new_unlabeled_files = self.get_new_unlabeled_files()
            
            if new_unlabeled_files:
                self.auto_timer_status_var.set(f"Final check: Found {len(new_unlabeled_files)} new files - monitoring stopped")
                
                # Log the discovery of new files
                self.logger.info(f"Stop button: Found {len(new_unlabeled_files)} new unlabeled files")
                for file_path in new_unlabeled_files:
                    self.logger.info(f"New file: {os.path.basename(file_path)}")
                
                # Update the CSV to mark these as unclassified
                for file_path in new_unlabeled_files:
                    self.labels[file_path] = "(Unclassified)"
                self.save_csv()
                self.update_counts()
                # Refresh the UI to show the new images
                self.apply_filter()
            else:
                self.auto_timer_status_var.set(f"[{current_time}] Final check: No new files found - monitoring stopped")
                self.logger.info("Stop button: No new unlabeled files found")
        
        # Update UI state
        if hasattr(self, 'auto_timer_enabled'):
            self.auto_timer_enabled.set(False)
        if hasattr(self, 'auto_timer_button'):
            self.auto_timer_button.config(text="Start", bg="#4CAF50", activebackground="#45a049")
        if hasattr(self, 'auto_timer_entry'):
            self.auto_timer_entry.config(state='normal')
        
        # Re-enable folder selection when monitoring is stopped
        self.enable_ui_controls_for_monitoring()

    def start_countdown(self, interval_minutes):
        """Start the countdown timer display"""
        from datetime import datetime, timedelta
        self.countdown_end_time = datetime.now() + timedelta(minutes=interval_minutes)
        self.update_countdown()

    def stop_countdown(self):
        """Stop the countdown timer display"""
        if self.countdown_job:
            self.root.after_cancel(self.countdown_job)
            self.countdown_job = None

    def update_countdown(self):
        """Update the countdown display every second"""
        if not self.auto_timer_enabled.get() or not self.countdown_end_time:
            return
            
        from datetime import datetime
        now = datetime.now()
        
        if now >= self.countdown_end_time:
            # Countdown finished
            self.auto_timer_status_var.set("Auto-classification running...")
            return
            
        # Calculate remaining time
        remaining = self.countdown_end_time - now
        total_seconds = int(remaining.total_seconds())
        
        if total_seconds > 60:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if seconds == 0:
                countdown_text = f"Next run in: {minutes}min"
            else:
                countdown_text = f"Next run in: {minutes}min {seconds}sec"
        else:
            countdown_text = f"Next run in: {total_seconds}sec"
        
        # Get current status without overwriting it
        current_status = self.auto_timer_status_var.get()
        # If current status contains countdown info, extract the base status
        if "Next run in:" in current_status:
            base_status = current_status.split("\nNext run in:")[0]
        else:
            base_status = current_status
            
        self.auto_timer_status_var.set(f"{base_status}\n{countdown_text}")
        
        # Schedule next update in 1 second
        self.countdown_job = self.root.after(1000, self.update_countdown)

    def scan_for_new_images(self):
        """Scan the folder for new images that weren't there before"""
        if not hasattr(self, 'folder_path') or not self.folder_path:
            return []
        
        # Get current files in folder
        try:
            current_files = [f for f in os.listdir(self.folder_path)
                           if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
            
            current_image_paths = []
            for f in current_files:
                current_image_paths.append(os.path.join(self.folder_path, f))
            
            current_image_paths.sort()
            
            # Find new images (not in self.all_image_paths)
            new_images = []
            if hasattr(self, 'all_image_paths'):
                new_images = [path for path in current_image_paths if path not in self.all_image_paths]
                
                # Update the all_image_paths list with new images
                if new_images:
                    self.all_image_paths.extend(new_images)
                    self.all_image_paths.sort()
            else:
                # If all_image_paths doesn't exist, all current images are "new"
                new_images = current_image_paths
                self.all_image_paths = current_image_paths
                
            return new_images
            
        except Exception as e:
            return []

    def run_auto_detection_timer(self):
        """Check for new unlabeled files every N minutes and optionally run auto-detection"""
        if not self.auto_timer_enabled.get():
            return
        
        # Update last run time and show execution
        from datetime import datetime
        self.last_auto_run = datetime.now()
        current_time = self.last_auto_run.strftime('%H:%M:%S')
        
        # Scan for new unlabeled files
        self.auto_timer_status_var.set(f"[{current_time}] Checking for new unlabeled files...")
        new_unlabeled_files = self.get_new_unlabeled_files()
        
        if new_unlabeled_files:
            self.auto_timer_status_var.set(f"Found {len(new_unlabeled_files)} new unlabeled files!")
            
            # Log the discovery of new files
            self.logger.info(f"Timer check: Found {len(new_unlabeled_files)} new unlabeled files")
            for file_path in new_unlabeled_files:
                self.logger.info(f"New file: {os.path.basename(file_path)}")
            
            # Check if auto-detection is enabled
            if self.auto_detect_enabled.get():
                self.auto_timer_status_var.set(f"Auto-detecting barcodes in {len(new_unlabeled_files)} new files...")
                # Run auto-detection on new files only
                self.process_auto_detection_on_new_files(new_unlabeled_files)
            else:
                self.auto_timer_status_var.set(f"Found {len(new_unlabeled_files)} new files")
                # Update the CSV to mark these as unclassified
                for file_path in new_unlabeled_files:
                    self.labels[file_path] = "(Unclassified)"
                self.save_csv()
                self.update_counts()
                # Refresh the UI to show the new images
                self.apply_filter()
        else:
            self.auto_timer_status_var.set(f"[{current_time}] No new unlabeled files found")
            self.logger.info("Timer check: No new unlabeled files found")
        
        # Schedule next run
        if self.auto_timer_enabled.get():
            try:
                interval_minutes = float(self.auto_timer_interval.get())
                interval_ms = int(interval_minutes * 60 * 1000)
                self.auto_timer_job = self.root.after(interval_ms, self.run_auto_detection_timer)
                
                # Restart countdown for next run
                self.start_countdown(interval_minutes)
            except ValueError:
                # If interval is invalid, stop the timer
                self.stop_auto_timer()

    def disable_ui_controls(self):
        """Disable all UI controls except the Stop button during auto-classification"""
        # Disable navigation buttons
        self.btn_prev.config(state='disabled')
        self.btn_first.config(state='disabled')
        self.btn_next.config(state='disabled')
        self.btn_jump_unclassified.config(state='disabled')
        
        # Disable radio buttons
        for rb in self.radio_buttons:
            rb.config(state='disabled')
        
        # Disable other buttons
        self.btn_select.config(state='disabled')
        self.btn_gen_no_read.config(state='disabled')
        self.btn_1to1.config(state='disabled')
        self.btn_zoom_in.config(state='disabled')
        self.btn_zoom_out.config(state='disabled')
        
        # Disable checkbox (COMMENTED OUT - AUTO DETECT HIDDEN)
        # self.auto_detect_checkbox.config(state='disabled')
        
        # Disable entry fields
        self.total_parcels_entry.config(state='disabled')
        # Note: auto_timer_entry is already disabled when timer is running

    def disable_ui_controls_for_monitoring(self):
        """Disable only folder selection during monitoring - keep radio buttons and filter active"""
        # Only disable folder selection
        self.btn_select.config(state='disabled')
        
        # Keep radio buttons, navigation, filter, and other controls enabled
        # This allows users to continue labeling while monitoring is active

    def enable_ui_controls(self):
        """Re-enable all UI controls after auto-classification completes"""
        # Enable navigation buttons
        self.btn_prev.config(state='normal')
        self.btn_first.config(state='normal')
        self.btn_next.config(state='normal')
        self.btn_jump_unclassified.config(state='normal')
        
        # Enable radio buttons
        for rb in self.radio_buttons:
            rb.config(state='normal')
        
        # Enable other buttons
        self.btn_select.config(state='normal')
        self.btn_gen_no_read.config(state='normal')
        self.btn_1to1.config(state='normal')
        self.btn_zoom_in.config(state='normal')
        self.btn_zoom_out.config(state='normal')
        
        # Enable checkbox (COMMENTED OUT - AUTO DETECT HIDDEN)
        # self.auto_detect_checkbox.config(state='normal')
        
        # Enable entry fields
        self.total_parcels_entry.config(state='normal')

    def enable_ui_controls_for_monitoring(self):
        """Re-enable folder selection after monitoring stops"""
        # Re-enable folder selection
        self.btn_select.config(state='normal')

    def process_auto_detection_silent(self, unclassified_images):
        """Process auto classification silently without popup dialogs"""
        total_images = len(unclassified_images)
        processed = 0
        no_code_count = 0
        read_failure_count = 0
        
        self.logger.info("-" * 50)
        self.logger.info("AUTO-CLASSIFICATION (TIMER) SESSION STARTED")
        self.logger.info(f"Unclassified images to process: {total_images}")
        
        for image_path in unclassified_images:
            # Update progress indicator
            processed += 1
            self.auto_timer_status_var.set(f"Processing {processed}/{total_images}\n{os.path.basename(image_path)}")
            self.root.update_idletasks()  # Force UI update
            
            # Get auto detection result
            detection_result = self.auto_detect_function(image_path)
            
            # Determine label based on result
            if detection_result == 0:
                label = "no code"
                no_code_count += 1
            else:  # detection_result > 0
                label = "read failure"
                read_failure_count += 1
            
            # Log the classification decision
            filename = os.path.basename(image_path)
            self.logger.info(f"TIMER-CLASSIFIED: {filename} → {label} (barcode count: {detection_result})")
            
            # Update labels dictionary
            if not hasattr(self, 'labels'):
                self.labels = {}
            self.labels[image_path] = label
            
            # If this is the currently displayed image, refresh the display immediately
            if (hasattr(self, 'image_paths') and self.image_paths and 
                self.current_index < len(self.image_paths) and 
                image_path == self.image_paths[self.current_index]):
                self.show_image()
        
        # Save to CSV and update statistics
        self.save_csv()
        self.update_total_stats()
        self.update_parcel_stats()
        self.update_progress_display()
        self.update_counts()
        
        # Log session summary
        completion_time = datetime.now().strftime("%H:%M:%S")
        self.logger.info("-" * 30)
        self.logger.info("AUTO-CLASSIFICATION (TIMER) SUMMARY:")
        self.logger.info(f"Total processed: {total_images}")
        self.logger.info(f"Classified as 'no code': {no_code_count}")
        self.logger.info(f"Classified as 'read failure': {read_failure_count}")
        self.logger.info(f"Completed at: {completion_time}")
        self.logger.info("AUTO-CLASSIFICATION (TIMER) SESSION COMPLETED")
        self.logger.info("-" * 50)
        
        # Update status with completion info
        self.auto_timer_status_var.set(f"Auto-classification complete at {completion_time}\nProcessed {total_images} images")

def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = ImageLabelTool(root)
    root.mainloop()

if __name__ == "__main__":
    # Protection for PyInstaller executables to prevent infinite loops
    multiprocessing.freeze_support()
    
    # Ensure PIL is available (already imported at top)
    try:
        # Test PIL import without re-importing
        Image.new('RGB', (1, 1))
    except Exception as e:
        messagebox.showerror("Missing Dependency", 
                           f"PIL/Pillow is not properly installed: {e}\n"
                           "Please install Pillow: pip install pillow")
        exit(1)
    
    # Run the main application
    main()
