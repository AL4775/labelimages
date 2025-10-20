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

# Optional imports for charting functionality
HAS_MATPLOTLIB = False
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    patches = None
    FigureCanvasTkAgg = None
    sns = None

# Application version
VERSION = "2.1.2"

LABELS = ["(Unclassified)", "no label", "read failure", "incomplete", "unreadable"]

class ImageLabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Aurora FIS Analytics INTERNAL tool v{VERSION}")
        
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "analytics_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # Fallback to PNG icon if ICO doesn't exist
                png_icon_path = os.path.join(os.path.dirname(__file__), "analytics_icon_32x32.png")
                if os.path.exists(png_icon_path):
                    from PIL import Image, ImageTk
                    icon_img = Image.open(png_icon_path)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.root.iconphoto(True, icon_photo)
        except Exception as e:
            # If icon loading fails, continue without icon
            print(f"Note: Could not load application icon: {e}")
        
        self.root.configure(bg="#FAFAFA")  # Very light gray background
        self.root.minsize(800, 500)  # Ultra-compact minimum window size
        self.root.geometry("1000x600")  # Ultra-compact window size
        self.image_paths = []
        self.current_index = 0
        self.labels = {}
        self.ocr_readable = {}  # Track OCR readable status per image
        self.comments = {}  # Track comments for each image
        self.folder_path = None
        self.csv_filename = None
        self.scale_1to1 = False  # Track if we're in 1:1 scale mode
        self.current_scale_factor = 1.0  # Track current scale factor
        self.zoom_level = 1.0  # Track zoom level for manual zoom
        self.pan_start_x = 0  # For mouse panning
        self.pan_start_y = 0  # For mouse panning
        
        # Track previously seen files for new file detection
        self.previously_seen_files = set()
        
        # Session index tracking - removed, no longer used
        # self.session_indices = {}  # Maps session_id to session_index
        # self.next_session_index = 1  # Next index to assign to a newly classified session
        
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
        
        # Top section: Folder selection and total sessions
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
                                         wraplength=400, justify=tk.LEFT, anchor="w", width=50)
        self.folder_path_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Total number of sessions input (right side)
        total_frame = tk.Frame(top_frame, bg="#FAFAFA")
        total_frame.pack(side=tk.RIGHT)
        tk.Label(total_frame, text="Number of effective sessions:", bg="#FAFAFA", font=("Arial", 11)).pack(side=tk.LEFT)
        self.total_sessions_var = tk.StringVar()
        self.total_sessions_entry = tk.Entry(total_frame, textvariable=self.total_sessions_var, width=8,
                                          font=("Arial", 11), bg="white", relief="solid", bd=1)
        self.total_sessions_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.total_sessions_entry.bind('<KeyRelease>', self.on_total_changed)
        
        # Filter dropdown (center)
        filter_frame = tk.Frame(top_frame, bg="#FAFAFA")
        filter_frame.pack(side=tk.LEFT, padx=(20, 0))
        tk.Label(filter_frame, text="Filter:", bg="#FAFAFA", font=("Arial", 10)).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="(Unclassified) only")
        filter_options = [
            "All images",
            "(Unclassified) only",
            "no label only",
            "read failure only",
            "incomplete only",
            "unreadable only",
            "OCR recovered only"
        ]
        self.filter_menu = tk.OptionMenu(filter_frame, self.filter_var, *filter_options, command=self.on_filter_changed)
        self.filter_menu.config(bg="#F5F5F5", font=("Arial", 10), relief="solid", bd=1)
        self.filter_menu.pack(side=tk.LEFT, padx=(5, 0))

        # Jump to Trigger ID frame (right side)
        jump_frame = tk.Frame(top_frame, bg="#FAFAFA")
        jump_frame.pack(side=tk.RIGHT, padx=(0, 20))
        tk.Label(jump_frame, text="Jump to:", bg="#FAFAFA", font=("Arial", 10)).pack(side=tk.LEFT)
        self.jump_trigger_var = tk.StringVar()
        self.jump_entry = tk.Entry(jump_frame, textvariable=self.jump_trigger_var, width=12, font=("Arial", 10))
        self.jump_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.jump_button = tk.Button(jump_frame, text="Go", command=self.jump_to_trigger_id, 
                                   bg="#CCCCCC", fg="white", font=("Arial", 9), relief="solid", bd=1, state=tk.DISABLED)
        self.jump_button.pack(side=tk.LEFT)
        
        # Initially disable jump entry as well since default filter is not "All images"
        self.jump_entry.config(state=tk.DISABLED)
        
        # Bind Enter key to jump function
        self.jump_entry.bind('<Return>', lambda event: self.jump_to_trigger_id())

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

        # Histogram equalization checkbox
        self.histogram_eq_enabled = tk.BooleanVar(value=False)
        self.histogram_eq_checkbox = tk.Checkbutton(toolbar_frame, text="📊 Hist EQ (Shift+H)", 
                                                   variable=self.histogram_eq_enabled,
                                                   command=self.on_histogram_eq_changed,
                                                   bg="#E8E8E8", font=("Arial", 9, "bold"),
                                                   selectcolor="white", padx=5, pady=2)
        self.histogram_eq_checkbox.pack(side=tk.LEFT, padx=(0, 10))

        # Export button for current filter
        self.btn_gen_filter_folder = tk.Button(toolbar_frame, text="Gen Filter Folder", 
                                             command=self.generate_filter_folder,
                                             bg="#9C27B0", fg="white", font=("Arial", 10, "bold"),
                                             padx=8, pady=3, relief="flat")
        self.btn_gen_filter_folder.pack(side=tk.LEFT, padx=(0, 5))

        # Export button for session IDs CSV
        self.btn_gen_sessions_csv = tk.Button(toolbar_frame, text="Gen Sessions CSV", 
                                            command=self.generate_sessions_csv,
                                            bg="#FF5722", fg="white", font=("Arial", 10, "bold"),
                                            padx=8, pady=3, relief="flat")
        self.btn_gen_sessions_csv.pack(side=tk.LEFT, padx=(0, 10))

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
            "no label": "#FFF3E0", 
            "read failure": "#FCE4EC", 
            "incomplete": "#E3F2FD",
            "unreadable": "#F1F8E9"
        }
        
        # Add keyboard shortcuts to labels
        label_shortcuts = {
            "(Unclassified)": "",
            "no label": " (Q)",
            "read failure": " (W)", 
            "incomplete": " (E)",
            "unreadable": " (R)"
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
        
        # OCR Readable checkbox (separate from radio buttons)
        ocr_frame = tk.Frame(label_frame, bg="#FAFAFA")
        ocr_frame.pack(pady=(8, 0))  # Add some space above the checkbox
        
        self.ocr_readable_var = tk.BooleanVar()
        self.ocr_checkbox = tk.Checkbutton(ocr_frame, text="OCR Readable (T)", 
                                         variable=self.ocr_readable_var,
                                         command=self.on_ocr_checkbox_changed,
                                         bg="#E8F5E8", font=("Arial", 11, "bold"),
                                         selectcolor="white", padx=5, pady=2)
        self.ocr_checkbox.pack()
        
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
        
        # Comment section for current image
        comment_section = tk.Frame(progress_tab, bg="#E3F2FD", relief="solid", bd=1, padx=6, pady=6)
        comment_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(comment_section, text="Current image comment", bg="#E3F2FD", font=("Arial", 12, "bold"), fg="#1976D2").pack()
        
        # Current image filename label
        self.current_image_filename_var = tk.StringVar()
        self.current_image_filename_label = tk.Label(comment_section, textvariable=self.current_image_filename_var,
                                                    bg="#E3F2FD", font=("Arial", 10, "bold"), fg="#424242",
                                                    justify=tk.LEFT, anchor="w")
        self.current_image_filename_label.pack(fill=tk.X, pady=(2, 5))
        
        # Comment text field
        comment_input_frame = tk.Frame(comment_section, bg="#E3F2FD")
        comment_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create frame for text widget and scrollbar
        text_frame = tk.Frame(comment_input_frame, bg="#E3F2FD")
        text_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Use Text widget for multiline comments instead of Entry
        self.comment_text = tk.Text(text_frame, 
                                   font=("Arial", 11), bg="#FFFFFF", fg="#333333",
                                   relief="solid", bd=1, height=3, wrap=tk.WORD)
        
        # Add scrollbar for the text widget
        comment_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.comment_text.yview)
        self.comment_text.config(yscrollcommand=comment_scrollbar.set)
        
        # Pack text widget and scrollbar
        self.comment_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        comment_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind comment text widget to save comment when it changes
        self.comment_text.bind('<KeyRelease>', self.on_comment_change)
        self.comment_text.bind('<FocusOut>', self.on_comment_change)
        
        # Track focus state for disabling keyboard shortcuts
        self.comment_text.bind('<FocusIn>', self.on_comment_focus_in)
        self.comment_text.bind('<FocusOut>', self.on_comment_focus_out)
        self.comment_has_focus = False
        
        # Comment info label
        self.comment_info_label = tk.Label(comment_section, text="💡 Add notes about the current image",
                                          bg="#E3F2FD", font=("Arial", 9), fg="#666666",
                                          justify=tk.LEFT, anchor="w")
        self.comment_info_label.pack(fill=tk.X)
        
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
        
        # Session statistics section
        session_section = tk.Frame(analysis_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        session_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(session_section, text="Session count", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#81C784").pack()
        self.session_count_var = tk.StringVar()
        self.session_count_label = tk.Label(session_section, textvariable=self.session_count_var, 
                                         font=("Arial", 13), bg="#F5F5F5", fg="#424242", wraplength=500,
                                         justify=tk.LEFT, anchor="w")
        self.session_count_label.pack(pady=(3, 0), fill=tk.X)
        
        # Total statistics section
        total_section = tk.Frame(analysis_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        total_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(total_section, text="Performance metrics", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#5E88D8").pack()
        self.session_stats_var = tk.StringVar()
        self.session_stats_label = tk.Label(total_section, textvariable=self.session_stats_var, 
                                         font=("Arial", 13), fg="#424242", bg="#F5F5F5", wraplength=500,
                                         justify=tk.LEFT, anchor="w")
        self.session_stats_label.pack(pady=(3, 0), fill=tk.X)

        # Pie chart button for session statistics
        pie_chart_frame = tk.Frame(analysis_tab, bg="#FAFAFA")
        pie_chart_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.btn_session_pie_chart = tk.Button(pie_chart_frame, text="📊 Show Session Pie Chart", 
                                            command=self.show_session_pie_chart,
                                            bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                                            relief="raised", bd=2, padx=10, pady=5)
        self.btn_session_pie_chart.pack(anchor="center")

        # === TAB 3: Log File Analysis ===
        log_file_tab = tk.Frame(stats_notebook, bg="#FAFAFA")
        stats_notebook.add(log_file_tab, text="Log File")
        
        # Log file selection section
        log_file_section = tk.Frame(log_file_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        log_file_section.pack(fill=tk.X, pady=(0, 6))
        
        tk.Label(log_file_section, text="Log File Analysis", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#9C27B0").pack()
        
        # File selection button
        select_button_frame = tk.Frame(log_file_section, bg="#F5F5F5")
        select_button_frame.pack(fill=tk.X, pady=(5, 5))
        
        self.btn_select_log_file = tk.Button(select_button_frame, text="📂 Select Log File", 
                                           command=self.select_log_file,
                                           bg="#CCCCCC", fg="#666666", font=("Arial", 10, "bold"),
                                           relief="raised", bd=2, padx=8, pady=3, state='disabled')
        self.btn_select_log_file.pack(side=tk.LEFT)
        
        # Refresh button next to the select button
        self.btn_refresh_log = tk.Button(select_button_frame, text="🔄 Refresh", 
                                        command=self.refresh_log_analysis,
                                        bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                        relief="raised", bd=2, padx=8, pady=3, state='disabled')
        self.btn_refresh_log.pack(side=tk.LEFT, padx=(5, 0))
        
        # Selected file label
        self.selected_log_file_var = tk.StringVar(value="No file selected")
        self.selected_log_file_label = tk.Label(log_file_section, textvariable=self.selected_log_file_var,
                                               bg="#F5F5F5", font=("Arial", 9), fg="#666666",
                                               wraplength=180, justify=tk.LEFT, anchor="w")
        self.selected_log_file_label.pack(fill=tk.X, pady=(2, 0))
        
        # Log analysis results section  
        log_results_section = tk.Frame(log_file_tab, bg="#F5F5F5", relief="solid", bd=1, padx=6, pady=6)
        log_results_section.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        
        tk.Label(log_results_section, text="Analysis Results", bg="#F5F5F5", font=("Arial", 12, "bold"), fg="#9C27B0").pack()
        
        # Results display area with scrollbar
        results_frame = tk.Frame(log_results_section, bg="#F5F5F5")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create scrollable text area
        self.log_results_text = tk.Text(results_frame, height=12, wrap=tk.WORD, 
                                       font=("Consolas", 9), bg="#FFFFFF", fg="#333333",
                                       relief="solid", bd=1, padx=5, pady=5)
        
        log_scrollbar = tk.Scrollbar(results_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_results_text.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.config(command=self.log_results_text.yview)
        
        # Initially disable text editing
        self.log_results_text.config(state=tk.DISABLED)
        
        # Export button for log analysis report
        export_button_frame = tk.Frame(log_results_section, bg="#F5F5F5")
        export_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.btn_export_log_report = tk.Button(export_button_frame, text="📄 Export Report", 
                                             command=self.export_log_analysis_report,
                                             bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                             relief="raised", bd=2, padx=12, pady=4, state='disabled')
        self.btn_export_log_report.pack(side=tk.LEFT)

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
        self.root.bind('<KeyPress-t>', self.label_shortcut_t)
        self.root.bind('<KeyPress-T>', self.label_shortcut_t)
        self.root.bind('<KeyPress-e>', self.label_shortcut_e)
        self.root.bind('<KeyPress-E>', self.label_shortcut_e)
        self.root.bind('<KeyPress-r>', self.label_shortcut_r)
        self.root.bind('<KeyPress-R>', self.label_shortcut_r)
        
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
        
        # Bind Shift+H for histogram equalization toggle
        self.root.bind('<Shift-H>', self.histogram_eq_shortcut)
        self.root.bind('<Shift-h>', self.histogram_eq_shortcut)
        
        # Set focus to root window to capture keyboard events
        self.root.focus_set()
        
        # Initialize button state based on default filter
        self.update_filter_button_state()
        
        # Initialize log file button state (disabled initially)
        self.update_log_file_button_state()

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
                self.btn_prev.config(state='disabled', bg='#CCCCCC', fg='#666666')
            if hasattr(self, 'btn_next'):
                self.btn_next.config(state='disabled', bg='#CCCCCC', fg='#666666')
            if hasattr(self, 'btn_jump_unclassified'):
                self.btn_jump_unclassified.config(state='disabled', bg='#CCCCCC', fg='#666666')
            return
        
        # Update Prev button
        if hasattr(self, 'btn_prev'):
            if self.current_index <= 0:
                self.btn_prev.config(state='disabled', bg='#CCCCCC', fg='#666666')
            else:
                self.btn_prev.config(state='normal', bg='#90CAF9', fg='black')
        
        # Update Next button  
        if hasattr(self, 'btn_next'):
            if self.current_index >= len(self.image_paths) - 1:
                self.btn_next.config(state='disabled', bg='#CCCCCC', fg='#666666')
            else:
                self.btn_next.config(state='normal', bg='#90CAF9', fg='black')
        
        # Update Next Unclassified button - only enabled when filter is "All images"
        if hasattr(self, 'btn_jump_unclassified'):
            filter_is_all = self.filter_var.get() == "All images"
            if not filter_is_all or not self.image_paths:
                self.btn_jump_unclassified.config(state='disabled', bg='#CCCCCC', fg='#666666')
            else:
                self.btn_jump_unclassified.config(state='normal', bg='#FF9800', fg='black')

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
            # Normalize all image paths consistently
            image_path = os.path.normpath(os.path.join(folder, f))
            self.all_image_paths.append(image_path)

        # Custom sort by trigger ID and sub-image count
        self.all_image_paths.sort(key=self.get_image_sort_key)
        self.current_index = 0
        self.labels = {}  # Reset labels for new folder
        self.comments = {}  # Reset comments for new folder
        
        # Initialize previously seen files with current files
        self.previously_seen_files = set(self.all_image_paths)
        
        self.load_csv()  # Try to load existing CSV if any
        self.auto_detect_total_groups()  # Auto-detect total number of sessions from filenames
        self.apply_filter()  # Apply current filter to show appropriate images
        
        # Update warning message and navigation buttons
        self.update_warning_message()
        self.update_navigation_buttons()
        self.update_log_file_button_state()  # Enable log file button when folder is selected
        
        # Set initial state for Jump to functionality after UI is fully initialized
        self.root.after_idle(self.update_jump_button_state)

    def get_image_sort_key(self, image_path):
        """
        Extract sorting key from image filename for proper ordering.
        Expected format: XXXXXXXXXX_XXXX_XXX_timestamp.jpg
        Returns tuple (trigger_id, sub_image_count) for sorting.
        """
        try:
            filename = os.path.basename(image_path)
            # Split by underscore to get parts
            parts = filename.split('_')
            
            if len(parts) >= 2:
                # First part: trigger ID (remove leading zeros for numeric comparison)
                trigger_id_str = parts[0]
                trigger_id = int(trigger_id_str) if trigger_id_str.isdigit() else 0
                
                # Second part: sub-image count
                sub_image_str = parts[1]
                sub_image_count = int(sub_image_str) if sub_image_str.isdigit() else 0
                
                return (trigger_id, sub_image_count)
            else:
                # Fallback to filename if parsing fails
                return (0, 0)
        except (ValueError, IndexError):
            # Fallback to filename sorting if parsing fails
            return (0, 0)

    def update_log_file_button_state(self):
        """Enable/disable the log file selection and refresh buttons based on folder selection"""
        if not hasattr(self, 'btn_select_log_file'):
            return
            
        if hasattr(self, 'folder_path') and self.folder_path:
            # Enable the select button when a folder is selected
            self.btn_select_log_file.config(state='normal', bg="#9C27B0", fg="white")
            
            # Enable refresh button only if a log file has been loaded
            if hasattr(self, 'btn_refresh_log'):
                if hasattr(self, 'current_log_content') and self.current_log_content:
                    self.btn_refresh_log.config(state='normal', bg="#4CAF50", fg="white")
                else:
                    self.btn_refresh_log.config(state='disabled', bg="#CCCCCC", fg="#666666")
        else:
            # Disable both buttons when no folder is selected
            self.btn_select_log_file.config(state='disabled', bg="#CCCCCC", fg="#666666")
            if hasattr(self, 'btn_refresh_log'):
                self.btn_refresh_log.config(state='disabled', bg="#CCCCCC", fg="#666666")
            
            # Clear any previous log file selection
            self.selected_log_file_var.set("No file selected")
            # Clear log results
            if hasattr(self, 'log_results_text'):
                self.log_results_text.config(state=tk.NORMAL)
                self.log_results_text.delete(1.0, tk.END)
                self.log_results_text.config(state=tk.DISABLED)

    def show_image(self):
        if not self.image_paths:
            self.canvas.delete("all")
            self.status_var.set("No images loaded.")
            self.scale_info_var.set("")
            return
        path = self.image_paths[self.current_index]
        img = Image.open(path)
        original_width, original_height = img.size
        
        # Apply histogram equalization if enabled
        if hasattr(self, 'histogram_eq_enabled') and self.histogram_eq_enabled.get():
            img = self.apply_histogram_equalization(img)
        
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
        
        # Update OCR readable checkbox status
        ocr_status = self.ocr_readable.get(path, False)
        self.ocr_readable_var.set(ocr_status)
        
        # Update comment field with current image's comment
        if hasattr(self, 'comment_text'):
            comment_text = self.comments.get(path, "")
            # Temporarily disable event bindings to prevent triggering on_comment_change during programmatic updates
            self.comment_text.unbind('<KeyRelease>')
            self.comment_text.unbind('<FocusOut>')
            
            # Clear and set the Text widget content
            self.comment_text.delete("1.0", tk.END)
            self.comment_text.insert("1.0", comment_text)
            
            # Re-bind the events after programmatic update is complete
            self.comment_text.bind('<KeyRelease>', self.on_comment_change)
            self.comment_text.bind('<FocusOut>', self.on_comment_change)
            
            # Update comment field state based on classification and filter status
            self.update_comment_field_state()
        
        # Update current image filename in comment section
        if hasattr(self, 'current_image_filename_var'):
            filename = os.path.basename(path)
            self.current_image_filename_var.set(f"📄 {filename}")
        
        self.status_var.set(f"{os.path.basename(path)} ({self.current_index+1}/{len(self.image_paths)}) - {original_width}x{original_height}px")
        
        # Update progress and label status
        self.update_progress_display()
        self.update_current_label_status()
        
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

    def jump_to_trigger_id(self):
        """Jump to the first image with the specified trigger ID."""
        if not self.image_paths:
            return
            
        # Check if filter is set to "All images"
        if self.filter_var.get() != "All images":
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Jump to Trigger ID", 
                                 "Jump to Trigger ID only works when filter is set to 'All images'.")
            return
        
        # Get the trigger ID from the input field
        trigger_id_input = self.jump_trigger_var.get().strip()
        if not trigger_id_input:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Jump to Trigger ID", "Please enter a Trigger ID.")
            return
        
        # Normalize the input (remove leading zeros if it's numeric)
        try:
            # If it's a number, convert to int then back to string to remove leading zeros
            if trigger_id_input.isdigit():
                normalized_trigger_id = str(int(trigger_id_input))
            else:
                normalized_trigger_id = trigger_id_input
        except ValueError:
            normalized_trigger_id = trigger_id_input
        
        # Search for the first image with the matching trigger ID
        for i, path in enumerate(self.image_paths):
            filename = os.path.basename(path)
            filename_without_ext = os.path.splitext(filename)[0]
            parts = filename_without_ext.split('_')
            
            if len(parts) >= 1:
                # Extract trigger ID (first part before underscore)
                file_trigger_id_str = parts[0]
                # Normalize the file trigger ID (remove leading zeros if numeric)
                try:
                    if file_trigger_id_str.isdigit():
                        file_trigger_id = str(int(file_trigger_id_str))
                    else:
                        file_trigger_id = file_trigger_id_str
                except ValueError:
                    file_trigger_id = file_trigger_id_str
                
                # Check if this trigger ID matches
                if file_trigger_id == normalized_trigger_id:
                    self.current_index = i
                    self.show_image()
                    # Clear the input field after successful jump
                    self.jump_trigger_var.set("")
                self.comment_text.delete("1.0", tk.END)
                self.comment_text.insert("1.0", comment_text)
                # Re-bind comment change events
                self.comment_text.bind('<KeyRelease>', self.on_comment_change)
                self.comment_text.bind('<FocusOut>', self.on_comment_change)
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Jump to Trigger ID", 
                           f"No image found with Trigger ID: {normalized_trigger_id}")

    def set_label(self, value):
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        self.labels[path] = value
        self.save_csv()
        self.update_counts()
        
        # Set image to fit-to-window mode after classification
        if self.scale_1to1:
            self.scale_1to1 = False
            self.zoom_level = 1.0
            self.btn_1to1.config(text="1:1 Scale", bg="#FFCC80")
            # Refresh the current image display to apply fit-to-window
            self.show_image()

    def set_label_radio(self):
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        
        self.labels[path] = self.label_var.get()
        self.save_csv()
        self.update_counts()
        self.update_session_stats()
        self.update_total_stats()
        self.update_progress_display()
        self.update_current_label_status()
        
        # Update comment field state based on new classification status
        self.update_comment_field_state()
        
        # Set image to fit-to-window mode after classification
        if self.scale_1to1:
            self.scale_1to1 = False
            self.zoom_level = 1.0
            self.btn_1to1.config(text="1:1 Scale", bg="#FFCC80")
        
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

    def on_ocr_checkbox_changed(self):
        """Handle OCR readable checkbox changes"""
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        
        self.ocr_readable[path] = self.ocr_readable_var.get()
        self.save_csv()
        self.update_counts()
        self.update_session_stats()
        self.update_total_stats()
        self.update_progress_display()
        self.update_current_label_status()

    def on_histogram_eq_changed(self):
        """Handle histogram equalization checkbox changes"""
        # Refresh the current image display to apply/remove histogram equalization
        if hasattr(self, 'image_paths') and self.image_paths:
            self.show_image()

    # Session index functionality removed - no longer used
    # def assign_session_index_if_needed(self, image_path):
    #     """Assign a session index to a session when it gets its first classification"""
    #     session_id = self.get_session_number(image_path)
    #     if not session_id:
    #         return  # No session ID, can't assign index
    #         
    #     # Check if this session already has an index
    #     if session_id in self.session_indices:
    #         return  # Already has an index
    #         
    #     # Check if this session has any classified images (other than the current one being set)
    #     session_has_classified_images = False
    #     for path in self.all_image_paths:
    #         if self.get_session_number(path) == session_id and path != image_path:
    #             if path in self.labels and self.labels[path] != "(Unclassified)":
    #                 session_has_classified_images = True
    #                 break
    #     
    #     # If this is the first classification for this session, assign an index
    #     if not session_has_classified_images:
    #         self.session_indices[session_id] = self.next_session_index
    #         self.next_session_index += 1

    # def get_session_index(self, image_path):
    #     """Get the session index for an image, or None if session is unclassified"""
    #     session_id = self.get_session_number(image_path)
    #     if not session_id:
    #         return None
    #     return self.session_indices.get(session_id, None)

    def label_shortcut_q(self, event=None):
        """Keyboard shortcut: Q for 'no label'"""
        if self.should_ignore_keyboard_shortcuts_new():
            return
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("no label")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_w(self, event=None):
        """Keyboard shortcut: W for 'read failure'"""
        if self.should_ignore_keyboard_shortcuts_new():
            return
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("read failure")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_t(self, event=None):
        """Keyboard shortcut: T for 'OCR readable' checkbox toggle"""
        if self.should_ignore_keyboard_shortcuts_new():
            return
        if self.image_paths:
            # Toggle the OCR readable checkbox
            current_value = self.ocr_readable_var.get()
            self.ocr_readable_var.set(not current_value)
            self.on_ocr_checkbox_changed()

    def label_shortcut_e(self, event=None):
        """Keyboard shortcut: E for 'incomplete'"""
        if self.should_ignore_keyboard_shortcuts_new():
            return
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("incomplete")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def label_shortcut_r(self, event=None):
        """Keyboard shortcut: R for 'unreadable'"""
        if self.should_ignore_keyboard_shortcuts_new():
            return
        if self.image_paths:
            # Check if current image was unclassified before setting new label
            current_path = self.image_paths[self.current_index]
            was_unclassified = current_path not in self.labels or self.labels[current_path] == "(Unclassified)"
            
            self.label_var.set("unreadable")
            self.set_label_radio()
            
            # Only jump to next unclassified if this image was previously unclassified
            if was_unclassified:
                self.jump_to_next_unclassified()

    def prev_image_shortcut(self, event=None):
        """Keyboard shortcut: Left arrow for previous image"""
        if self.should_ignore_keyboard_shortcuts():
            return
        self.prev_image()

    def next_image_shortcut(self, event=None):
        """Keyboard shortcut: Right arrow for next image"""
        if self.should_ignore_keyboard_shortcuts():
            return
        self.next_image()

    def go_to_first_image_shortcut(self, event=None):
        """Keyboard shortcut: Home key for go to first image"""
        if self.should_ignore_keyboard_shortcuts():
            return
        self.go_to_first_image()

    def scale_1to1_shortcut(self, event=None):
        """Keyboard shortcut: Shift+O for 1:1 scale (always force true 1:1)"""
        if self.should_ignore_keyboard_shortcuts():
            return
        # Always force to true 1:1 scale regardless of current state
        self.scale_1to1 = True
        self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
        self.zoom_level = 1.0  # Force reset zoom level to true 1:1
        # Always refresh the current image display to apply true 1:1 scale
        if hasattr(self, 'image_paths') and self.image_paths:
            self.show_image()

    def fit_window_shortcut(self, event=None):
        """Keyboard shortcut: Shift+W for fit-to-window (always set to fit)"""
        if self.should_ignore_keyboard_shortcuts():
            return
        # Always set to fit mode regardless of current state
        if self.scale_1to1:
            self.scale_1to1 = False
            self.zoom_level = 1.0
            self.btn_1to1.config(text="1:1 Scale", bg="#FFCC80")
            # Refresh the current image display
            if hasattr(self, 'image_paths') and self.image_paths:
                self.show_image()

    def histogram_eq_shortcut(self, event=None):
        """Keyboard shortcut: Shift+H for histogram equalization toggle"""
        if self.should_ignore_keyboard_shortcuts():
            return
        # Toggle the histogram equalization checkbox
        if hasattr(self, 'histogram_eq_enabled'):
            current_value = self.histogram_eq_enabled.get()
            self.histogram_eq_enabled.set(not current_value)
            # Trigger the callback to refresh the image
            self.on_histogram_eq_changed()

    def on_total_changed(self, event=None):
        """Called when the total sessions field changes"""
        self.update_total_stats()
        # Trigger CSV and stats refresh when total sessions changes
        self.save_csv()

    def on_filter_changed(self, value=None):
        """Called when the filter dropdown changes"""
        self.apply_filter()
        self.update_filter_button_state()
        self.update_jump_button_state()
        # Update comment field state when filter changes
        self.update_comment_field_state()

    def on_comment_change(self, *args):
        """Called when the comment text field changes"""
        if hasattr(self, 'image_paths') and self.image_paths and self.current_index < len(self.image_paths):
            current_path = self.image_paths[self.current_index]
            # Get text from Text widget instead of StringVar
            comment_text = self.comment_text.get("1.0", tk.END).strip()
            
            # Store comment for current image
            if comment_text:
                self.comments[current_path] = comment_text
            else:
                # Remove empty comments
                if current_path in self.comments:
                    del self.comments[current_path]
            
            # Save CSV immediately when comment changes
            self.save_csv()

    def on_comment_focus_in(self, event=None):
        """Called when comment text widget gains focus"""
        # Only allow focus if image is classified AND not in "All images" mode
        is_all_images_filter = self.filter_var.get() == "All images"
        if self.is_current_image_unclassified() or is_all_images_filter:
            # Remove focus from comment field if image is unclassified or in All images mode
            self.root.focus_set()  # Set focus back to main window
            return
        self.comment_has_focus = True

    def on_comment_focus_out(self, event=None):
        """Called when comment text widget loses focus"""
        self.comment_has_focus = False
        # Also save comment when focus is lost
        self.on_comment_change()

    def should_ignore_keyboard_shortcuts(self):
        """Check if keyboard shortcuts should be ignored (e.g., when typing in comment field)"""
        return getattr(self, 'comment_has_focus', False)

    def is_current_image_unclassified(self):
        """Check if the current image is unclassified"""
        if not hasattr(self, 'image_paths') or not self.image_paths or self.current_index >= len(self.image_paths):
            return False
        
        current_path = self.image_paths[self.current_index]
        return current_path not in self.labels or self.labels[current_path] == "(Unclassified)"

    def should_ignore_keyboard_shortcuts_new(self):
        """Check if keyboard shortcuts should be ignored"""
        # Ignore if typing in comment field
        if getattr(self, 'comment_has_focus', False):
            return True
        
        # Ignore if current image is already classified (only allow shortcuts on unclassified images)
        if not self.is_current_image_unclassified():
            return True
            
        return False

    def update_comment_field_state(self):
        """Update comment field enabled/disabled state based on classification status and filter"""
        if hasattr(self, 'comment_text'):
            # Disable comment field if image is unclassified OR if viewing "All images"
            is_all_images_filter = self.filter_var.get() == "All images"
            is_unclassified = self.is_current_image_unclassified()
            
            if is_unclassified and not is_all_images_filter:
                # Disable for unclassified images (when not in All images mode)
                self.comment_text.config(state='disabled', bg='#F0F0F0', fg='#888888')
                if hasattr(self, 'comment_info_label'):
                    self.comment_info_label.config(text="💡 Classify image first to add comments", fg="#888888")
            elif is_all_images_filter:
                # Disable for All images filter mode
                self.comment_text.config(state='disabled', bg='#F0F0F0', fg='#888888')
                if hasattr(self, 'comment_info_label'):
                    self.comment_info_label.config(text="💡 Comments disabled in 'All images' view", fg="#888888")
            else:
                # Enable comment field for classified images in filtered views
                self.comment_text.config(state='normal', bg='#FFFFFF', fg='#333333')
                if hasattr(self, 'comment_info_label'):
                    self.comment_info_label.config(text="💡 Add notes about the current image", fg="#666666")

    def update_jump_button_state(self):
        """Enable/disable jump functionality based on current filter"""
        try:
            if hasattr(self, 'jump_button') and hasattr(self, 'jump_entry'):
                if self.filter_var.get() == "All images":
                    # Enable jump functionality
                    self.jump_button.config(state=tk.NORMAL, bg="#4CAF50")
                    self.jump_entry.config(state=tk.NORMAL)
                else:
                    # Disable jump functionality
                    self.jump_button.config(state=tk.DISABLED, bg="#CCCCCC")
                    self.jump_entry.config(state=tk.DISABLED)
        except Exception as e:
            # Silently handle any UI update errors during initialization
            pass

    def show_session_pie_chart(self):
        """Display a modal dialog with pie chart for session statistics"""
        if not HAS_MATPLOTLIB:
            messagebox.showwarning("Charts Unavailable", 
                                 "Chart functionality is not available.\n"
                                 "Matplotlib is required for charts but not installed.\n"
                                 "The main application works without charts.")
            return
            
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            messagebox.showwarning("No Data", "Please select a folder with images first.")
            return
        
        # Calculate session statistics
        session_data = self.calculate_session_stats_for_chart()
        if not session_data:
            messagebox.showinfo("No Data", "No classified sessions found to display in pie chart.")
            return
        
        # Create modal dialog
        pie_dialog = tk.Toplevel(self.root)
        pie_dialog.title(f"Session Statistics Pie Chart - Aurora FIS Analytics INTERNAL tool v{VERSION}")
        pie_dialog.geometry("800x650")
        pie_dialog.configure(bg="#FAFAFA")
        pie_dialog.transient(self.root)  # Make it modal
        pie_dialog.grab_set()  # Make it modal
        
        # Center the dialog
        pie_dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Create the pie chart and store references for cleanup
        chart_canvas, chart_figure = self.create_session_pie_chart_in_dialog(pie_dialog, session_data)
        
        # Function to properly close the dialog and cleanup matplotlib resources
        def close_pie_dialog():
            try:
                if chart_canvas:
                    chart_canvas.get_tk_widget().destroy()
                if chart_figure:
                    plt.close(chart_figure)
            except:
                pass  # Ignore any cleanup errors
            pie_dialog.destroy()
        
        # Add close button
        close_frame = tk.Frame(pie_dialog, bg="#FAFAFA")
        close_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        close_btn = tk.Button(close_frame, text="Close", command=close_pie_dialog,
                             bg="#757575", fg="white", font=("Arial", 11, "bold"),
                             relief="raised", bd=2, padx=20, pady=5)
        close_btn.pack(anchor="center")
        
        # Also bind the window close event to our cleanup function
        pie_dialog.protocol("WM_DELETE_WINDOW", close_pie_dialog)

    def calculate_session_stats_for_chart(self):
        """Calculate session statistics for pie chart display using the same logic as Net Stats"""
        # Get the total number from the UI field
        try:
            total_entered = int(self.total_sessions_var.get()) if self.total_sessions_var.get() else 0
        except ValueError:
            messagebox.showwarning("Invalid Data", "Please enter a valid total number of sessions first.")
            return {}

        if total_entered <= 0:
            messagebox.showwarning("Invalid Data", "Total number of sessions must be greater than 0.")
            return {}

        # Get current session statistics using the same logic as the Net Stats
        session_labels_dict = self.calculate_session_labels()
        actual_sessions = len(session_labels_dict)
        
        sessions_no_code = 0
        sessions_read_failure = 0
        sessions_ocr_readable = 0
        
        for session_label in session_labels_dict.values():
            if session_label == "no label":
                sessions_no_code += 1
            elif session_label == "read failure":
                sessions_read_failure += 1
        
        # Calculate sessions with OCR readable images (separate from primary classification)
        sessions_ocr_readable = self.calculate_sessions_with_ocr_readable()
        
        # Calculate sessions with unreadable code (excluding no_code and read_failure)
        sessions_unreadable_code = actual_sessions - sessions_no_code - sessions_read_failure
        
        # Calculate readable sessions using NEW formulas:
        # Total readable w/o OCR = total entered - session number + read failure
        total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
        
        # Calculate OCR readable sessions that are NOT read failure sessions
        sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
        
        # Total readable w/ OCR = Total readable w/o OCR + OCR readable sessions that are not read failure
        total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
        
        # Calculate successful reads (using w/ OCR total)
        sessions_successful_reads = total_readable_incl_ocr - sessions_read_failure
        
        print(f"DEBUG: Using NEW calculation formulas:")
        print(f"  - Total entered: {total_entered}")
        print(f"  - Actual sessions found: {actual_sessions}")
        print(f"  - Sessions no label: {sessions_no_code}")
        print(f"  - Sessions read failure: {sessions_read_failure}")
        print(f"  - Sessions with OCR readable: {sessions_ocr_readable}")
        print(f"  - Sessions OCR readable (non-failure): {sessions_ocr_readable_non_failure}")
        print(f"  - Sessions unreadable code: {sessions_unreadable_code}")
        print(f"  - Total readable (excl OCR): {total_readable_excl_ocr}")
        print(f"  - Total readable (incl OCR): {total_readable_incl_ocr}")
        print(f"  - Successful reads: {sessions_successful_reads}")
        
        # Build result dictionary
        session_stats = {}
        if sessions_no_code > 0:
            session_stats["Sessions with no label"] = sessions_no_code
        if sessions_read_failure > 0:
            session_stats["Sessions with Read Failure"] = sessions_read_failure
        if sessions_ocr_readable > 0:
            session_stats["Sessions with OCR Recovered"] = sessions_ocr_readable
        if sessions_unreadable_code > 0:
            session_stats["Sessions with Unreadable Code"] = sessions_unreadable_code
        if sessions_successful_reads > 0:
            session_stats["Sessions with Successful Reads"] = sessions_successful_reads
        
        print(f"DEBUG: Final pie chart data: {session_stats}")
        
        return session_stats

    def create_session_pie_chart_in_dialog(self, parent, session_data):
        """Create a pie chart showing session statistics in the given parent widget"""
        if not HAS_MATPLOTLIB:
            return None, None
        
        # Set up matplotlib style
        plt.style.use('default')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(9, 6))
        fig.patch.set_facecolor('#FAFAFA')
        
        # Prepare data
        labels = list(session_data.keys())
        sizes = list(session_data.values())
        
        # Convert labels to multi-line format for better fit
        formatted_labels = []
        for label in labels:
            if "Sessions with" in label:
                # Split "Sessions with X" into two lines
                parts = label.split(" with ")
                if len(parts) == 2:
                    formatted_labels.append(f"Sessions with\n{parts[1]}")
                else:
                    formatted_labels.append(label)
            else:
                formatted_labels.append(label)
        
        # Define colors for different statuses
        color_map = {
            "Sessions with no label": "#FF5722",          # Deep Orange/Red
            "Sessions with Read Failure": "#F44336",     # Red
            "Sessions with OCR Recovered": "#2196F3",     # Blue
            "Sessions with Unreadable Code": "#FF9800",  # Orange
            "Sessions with Successful Reads": "#4CAF50"  # Green
        }
        
        colors = [color_map.get(label, "#9E9E9E") for label in labels]
        
        # Create pie chart with formatted multi-line labels
        wedges, texts, autotexts = ax.pie(sizes, labels=formatted_labels, colors=colors, autopct='%1.1f%%',
                                         startangle=90, textprops={'fontsize': 9, 'ha': 'center'})
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Improve label text positioning and formatting
        for text in texts:
            text.set_fontweight('bold')
            text.set_fontsize(9)
        
        ax.set_title('Session Classification Status Distribution', fontsize=14, fontweight='bold', pad=20)
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        return canvas, fig

    def select_log_file(self):
        """Open file dialog to select a log file for analysis"""
        from tkinter import filedialog
        
        # Determine initial directory - use the selected folder if available
        if hasattr(self, 'folder_path') and self.folder_path:
            initial_dir = self.folder_path
        else:
            initial_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Open file dialog for log files
        file_path = filedialog.askopenfilename(
            title="Select Log File for Analysis",
            filetypes=[
                ("All files", "*.*")
            ],
            initialdir=initial_dir
        )
        
        if file_path:
            # Update selected file label
            filename = os.path.basename(file_path)
            self.selected_log_file_var.set(f"Selected: {filename}")
            
            # Analyze the log file
            self.analyze_log_file(file_path)
    
    def analyze_log_file(self, file_path):
        """Analyze the selected log file and display results"""
        try:
            # Clear previous results
            self.log_results_text.config(state=tk.NORMAL)
            self.log_results_text.delete(1.0, tk.END)
            
            # Read and parse the log file
            with open(file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Store log content for later use (date range extraction, etc.)
            self.current_log_content = log_content
            
            # Analyze the log content
            analysis_results = self.parse_log_content(log_content)
            
            # Display results
            self.display_log_analysis_results(analysis_results)
            
            # Enable the refresh button now that we have log content
            self.update_log_file_button_state()
            
        except Exception as e:
            # Display error message
            self.log_results_text.config(state=tk.NORMAL)
            self.log_results_text.delete(1.0, tk.END)
            self.log_results_text.insert(tk.END, f"Error analyzing log file:\n{str(e)}")
            self.log_results_text.config(state=tk.DISABLED)
    
    def refresh_log_analysis(self):
        """Refresh the log analysis by reloading the current log file and recalculating all values"""
        if not hasattr(self, 'current_log_content') or not self.current_log_content:
            messagebox.showwarning("No Log File", "Please select a log file first before refreshing.")
            return
            
        try:
            # Clear previous results
            self.log_results_text.config(state=tk.NORMAL)
            self.log_results_text.delete(1.0, tk.END)
            self.log_results_text.insert(tk.END, "Refreshing analysis...\n")
            self.log_results_text.config(state=tk.DISABLED)
            
            # Force update the UI
            self.root.update()
            
            # Re-analyze the stored log content
            analysis_results = self.parse_log_content(self.current_log_content)
            
            # Force recalculation of all session and image statistics
            self.update_counts()
            self.update_session_stats() 
            self.update_total_stats()
            self.update_progress_display()
            
            # Display refreshed results
            self.display_log_analysis_results(analysis_results)
            
            # Show success message in the log results area temporarily
            current_text = self.log_results_text.get(1.0, tk.END)
            self.log_results_text.config(state=tk.NORMAL)
            self.log_results_text.insert(1.0, "✓ Analysis refreshed successfully!\n\n")
            self.log_results_text.config(state=tk.DISABLED)
            
        except Exception as e:
            # Display error message
            self.log_results_text.config(state=tk.NORMAL)
            self.log_results_text.delete(1.0, tk.END)
            self.log_results_text.insert(tk.END, f"Error refreshing log analysis:\n{str(e)}")
            self.log_results_text.config(state=tk.DISABLED)
            messagebox.showerror("Refresh Error", f"Failed to refresh log analysis:\n{str(e)}")
    
    def parse_log_content(self, log_content):
        """Parse log content and extract statistics"""
        import re
        
        # Get list of image files in the selected folder to cross-reference
        saved_image_ids = set()
        if hasattr(self, 'folder_path') and self.folder_path:
            try:
                # Get all image files and extract trigger IDs from filenames
                image_files = [f for f in os.listdir(self.folder_path)
                             if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
                
                # Extract trigger IDs from filenames (format: XXXXXXXXXX_XXXX_XXX_timestamp.jpg)
                # The trigger ID is the first part before the first underscore, with leading zeros removed
                for filename in image_files:
                    # Extract the first part before underscore
                    parts = filename.split('_')
                    if parts and len(parts[0]) >= 10:  # Should be 10 digits
                        trigger_id_str = parts[0]
                        # Convert to integer to remove leading zeros, then back to string
                        try:
                            trigger_id = str(int(trigger_id_str))
                            saved_image_ids.add(trigger_id)
                        except ValueError:
                            continue  # Skip if not a valid number
            except Exception:
                # If we can't read the folder, continue without cross-reference
                pass
        
        # Initialize counters and tracking lists
        unique_ids = set()
        false_triggers = 0
        timeouts = 0
        total_entries = 0
        total_noread = 0         # Track total NOREAD entries
        missed_trigger_ids = []  # Track IDs with false triggers (no corresponding saved image)
        timeout_ids = []         # Track IDs with timeouts
        
        # Split into lines
        lines = log_content.split('\n')
        
        # Patterns to look for
        id_pattern = r'ID:\s*(\d+)'  # Look for "ID: " followed by digits
        false_trigger_patterns = [
            r'false.trigger',
            r'no.code.detected',
            r'empty.result',
            r'detection.failed'
            # Note: removed 'noread' from here - we'll handle NOREAD separately
        ]
        timeout_patterns = [
            r'timeout',
            r'timed.out',
            r'no.response'
        ]
        
        # Process each line
        for line in lines:
            original_line = line.strip()  # Keep original case for ID extraction
            line_lower = line.strip().lower()  # Lowercase for pattern matching
            if not original_line:
                continue
                
            total_entries += 1
            
            # Extract unique IDs from original case line
            id_matches = re.findall(id_pattern, original_line)
            current_line_ids = []
            for id_match in id_matches:
                unique_ids.add(id_match)
                current_line_ids.append(id_match)
            
            # Check for false triggers in lowercase
            is_false_trigger = False
            for pattern in false_trigger_patterns:
                if re.search(pattern, line_lower):
                    false_triggers += 1
                    is_false_trigger = True
                    # Add all IDs from this line to missed triggers
                    for id_val in current_line_ids:
                        missed_trigger_ids.append(id_val)
                    break
            
            # Special handling for NOREAD - only consider it a missed trigger if no saved image exists
            if not is_false_trigger and 'noread' in line_lower:
                total_noread += 1  # Count all NOREAD entries
                for id_val in current_line_ids:
                    # Only mark as missed trigger if there's no corresponding saved image
                    if id_val not in saved_image_ids:
                        false_triggers += 1
                        missed_trigger_ids.append(id_val)
                        is_false_trigger = True
            
            # Check for timeouts in lowercase (only if not already a false trigger)
            if not is_false_trigger:
                for pattern in timeout_patterns:
                    if re.search(pattern, line_lower):
                        timeouts += 1
                        # Add all IDs from this line to timeouts
                        for id_val in current_line_ids:
                            timeout_ids.append(id_val)
                        break
        
        # Calculate effective session count
        # Effective count = unique IDs - false triggers - timeouts
        effective_session_count = len(unique_ids) - false_triggers - timeouts
        if effective_session_count < 0:
            effective_session_count = 0
        
        return {
            'total_entries': total_entries,
            'unique_ids': len(unique_ids),
            'unique_id_list': sorted(list(unique_ids)),
            'false_triggers': false_triggers,
            'timeouts': timeouts,
            'total_noread': total_noread,
            'effective_session_count': effective_session_count,
            'missed_trigger_ids': missed_trigger_ids,
            'timeout_ids': timeout_ids
        }
    
    def display_log_analysis_results(self, results):
        """Display the log analysis results in the structured format requested"""
        self.log_results_text.config(state=tk.NORMAL)
        self.log_results_text.delete(1.0, tk.END)
        
        # Store results for potential export
        self.current_log_analysis = results
        
        # Auto-update "Total number of sessions" field with effective session count
        effective_session_count = results.get('effective_session_count', 0)
        if effective_session_count > 0:
            # Update the total sessions field
            self.total_sessions_var.set(str(effective_session_count))
            
            # Refresh all statistics and analysis
            self.update_session_stats()
            self.update_total_stats()
            self.update_progress_display()
            self.update_counts()
            
            # Save the updated CSV with the new total
            self.save_csv()
        
        # Extract start/end dates from log file if available
        log_date_info = self.extract_log_date_range()
        
        # Get updated analysis data after the total parcels change
        analysis_data = self.get_analysis_data()
        
        # Format and display results in the requested structure
        output = []
        
        # PATH section
        output.append("=== PATH ===")
        if hasattr(self, 'folder_path') and self.folder_path:
            output.append(f"Folder Path: {self.folder_path}")
        else:
            output.append("Folder Path: No folder selected")
        
        output.append("")  # Empty line
        
        # DATES section
        output.append("=== DATES ===")
        if log_date_info:
            output.append(f"Start Date: {log_date_info['start_date']}")
            output.append(f"End Date: {log_date_info['end_date']}")
        else:
            output.append("Start Date: Not available")
            output.append("End Date: Not available")
        
        output.append("")  # Empty line
        
        # LOG FILE ANALYSIS section
        output.append("=== LOG FILE ANALYSIS ===")
        output.append(f"Number of sessions: {results['unique_ids']}")
        
        # Calculate read vs noread sessions
        total_noread = results.get('total_noread', 0)
        unique_ids = results['unique_ids']
        read_sessions = unique_ids - total_noread
        
        output.append(f"Number of Read sessions: {read_sessions}")
        output.append(f"Number of No-Read sessions: {total_noread}")
        output.append(f"Number of False triggers: {results['false_triggers']}")
        output.append(f"Number of Effective sessions: {results['effective_session_count']}")
        
        output.append("")  # Empty line
        
        # READING ANALYSIS section
        output.append("=== READING ANALYSIS ===")
        
        # Calculate fail reading parcels (NOREAD minus missed triggers)
        fail_reading_parcels = total_noread - results['false_triggers']
        if fail_reading_parcels < 0:
            fail_reading_parcels = 0
            
        output.append(f"Number of Failed sessions: {fail_reading_parcels}")
        output.append(f"Number of No-Code sessions: {analysis_data['no_code_count']}")
        output.append(f"Number of Read-Failure sessions: {analysis_data['read_failure_count']}")
        
        # Calculate total unreadable using same formula as Analysis tab
        ocr_readable_count = analysis_data.get('ocr_readable_count', 0)
        # Use consistent formula: total_sessions - sessions_no_code - sessions_read_failure
        total_unreadable = len(self.calculate_session_labels()) - analysis_data['no_code_count'] - analysis_data['read_failure_count']
        if total_unreadable < 0:
            total_unreadable = 0
            
        output.append(f"Number of Unreadable sessions: {total_unreadable}")
        output.append(f"Number of OCR recovered sessions: {ocr_readable_count}")
        
        output.append("")  # Empty line
        
        # READ RATE section
        output.append("=== READ RATE ===")
        
        # Calculate rates
        gross_rate = self.calculate_gross_rate(results, analysis_data)
        net_reading_performance = self.calculate_net_reading_performance(results, analysis_data)
        
        output.append(f"Gross read performance: {gross_rate:.1f}%")
        output.append(f"Net read performance (excl. OCR): {net_reading_performance['excl_ocr']:.2f}%")
        output.append(f"Net read performance (incl. OCR): {net_reading_performance['incl_ocr']:.2f}%")
        
        # Add OCR improvement percentage
        if net_reading_performance['excl_ocr'] >= 0 and net_reading_performance['incl_ocr'] >= 0:
            # Get analysis data to calculate actual read numbers
            total_entered = analysis_data.get('total_entered', 0)
            actual_sessions = analysis_data.get('actual_sessions', 0)
            sessions_read_failure = analysis_data.get('read_failure_count', 0)
            sessions_ocr_readable = self.calculate_sessions_with_ocr_readable()
            sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
            
            # Calculate readable sessions and read images
            total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
            total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
            
            read_images_excl_ocr = total_readable_excl_ocr - sessions_read_failure
            read_images_incl_ocr = read_images_excl_ocr + sessions_ocr_readable
            
            if read_images_excl_ocr > 0:
                # Formula: [(Read w/ OCR - Read w/o OCR) / Read w/o OCR] × 100
                ocr_improvement = ((read_images_incl_ocr - read_images_excl_ocr) / read_images_excl_ocr) * 100
                output.append(f"OCR read rate improvement: +{ocr_improvement:.2f}%")
            else:
                output.append("OCR read rate improvement: N/A (no baseline reads)")
        
        # Join and display
        result_text = "\n".join(output)
        self.log_results_text.insert(tk.END, result_text)
        self.log_results_text.config(state=tk.DISABLED)
        
        # Enable export button
        self.enable_export_button()
        
        # Generate CSV file with missed triggers and timeouts (existing functionality)
        self.generate_issues_csv(results)
    
    def extract_date_from_images(self):
        """Extract date from image filenames (format: day-month-year)"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return None
            
        try:
            # Try the first few images in case the first one has an unusual format
            for image_path in self.all_image_paths[:5]:
                filename = os.path.basename(image_path)
                
                # Try to extract date from this filename
                date_found = self.extract_date_from_filename(filename)
                if date_found:
                    return date_found
                    
        except Exception as e:
            print(f"DEBUG: Error extracting date from images: {e}")
            
        return None
    
    def extract_date_from_filename(self, filename):
        """Extract date from a single filename"""
        try:
            import re
            
            # Method 1: Extract timestamp from filename parts
            parts = filename.split('_')
            if len(parts) >= 4:
                timestamp_part = parts[-1].split('.')[0]  # Remove extension
                
                # Case 1: YYYYMMDD format (exactly 8 digits)
                if len(timestamp_part) == 8 and timestamp_part.isdigit():
                    year = timestamp_part[:4]
                    month = timestamp_part[4:6]
                    day = timestamp_part[6:8]
                    return f"{day}-{month}-{year}"
                
                # Case 2: YYYYMMDD_HHMMSS or YYYYMMDDHHMMSS format
                if len(timestamp_part) >= 8:
                    date_part = timestamp_part[:8]
                    if date_part.isdigit() and len(date_part) == 8:
                        year = date_part[:4]
                        month = date_part[4:6]
                        day = date_part[6:8]
                        return f"{day}-{month}-{year}"
                        
                # Case 3: Check other parts for date
                for part in parts:
                    if len(part) >= 8 and part[:8].isdigit():
                        date_part = part[:8]
                        year = date_part[:4]
                        month = date_part[4:6]
                        day = date_part[6:8]
                        # Validate date ranges
                        if 2020 <= int(year) <= 2030 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                            return f"{day}-{month}-{year}"
            
            # Method 2: Find YYYYMMDD pattern anywhere in filename using regex
            date_pattern = re.search(r'(20\d{2})(\d{2})(\d{2})', filename)
            if date_pattern:
                year = date_pattern.group(1)
                month = date_pattern.group(2)
                day = date_pattern.group(3)
                # Validate date ranges
                if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    return f"{day}-{month}-{year}"
            
            # Method 3: Look for different date patterns
            other_patterns = [
                r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
                r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
                r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            ]
            
            for pattern in other_patterns:
                match = re.search(pattern, filename)
                if match:
                    if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD format
                        year, month, day = match.groups()
                    else:  # DD-MM-YYYY or DD/MM/YYYY format
                        day, month, year = match.groups()
                    
                    # Validate date ranges
                    if 2020 <= int(year) <= 2030 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                        return f"{day}-{month}-{year}"
                        
        except Exception as e:
            print(f"DEBUG: Error extracting date from filename {filename}: {e}")
            
        return None
    
    def extract_log_date_range(self):
        """Extract start and end dates from log file based on smallest and largest ID entries"""
        if not hasattr(self, 'current_log_content') or not self.current_log_content:
            return None
        
        try:
            import re
            from datetime import datetime
            
            # Extract all lines with timestamps and IDs
            lines = self.current_log_content.split('\n')
            entries = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for ID pattern
                id_matches = re.findall(r'ID:\s*(\d+)', line)
                if not id_matches:
                    continue
                
                # Try to extract timestamp from the line
                # Common log timestamp patterns
                timestamp_patterns = [
                    r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',  # YYYY-MM-DD HH:MM:SS
                    r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',  # MM/DD/YYYY HH:MM:SS
                    r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})',  # DD-MM-YYYY HH:MM:SS
                    r'(\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2})',        # YYYYMMDD_HHMMSS
                    r'(\d{8}_\d{6})',                            # YYYYMMDD_HHMMSS
                ]
                
                timestamp = None
                for pattern in timestamp_patterns:
                    match = re.search(pattern, line)
                    if match:
                        timestamp = match.group(1)
                        break
                
                # If timestamp found, store entry
                if timestamp:
                    for id_val in id_matches:
                        entries.append({
                            'id': int(id_val) if id_val.isdigit() else 0,
                            'timestamp': timestamp,
                            'raw_line': line
                        })
            
            if not entries:
                return None
            
            # Sort by ID to find smallest and largest
            entries.sort(key=lambda x: x['id'])
            
            start_entry = entries[0]
            end_entry = entries[-1]
            
            # Format the timestamps
            start_date = self.format_log_timestamp(start_entry['timestamp'])
            end_date = self.format_log_timestamp(end_entry['timestamp'])
            
            return {
                'start_date': start_date,
                'end_date': end_date,
                'start_id': start_entry['id'],
                'end_id': end_entry['id']
            }
            
        except Exception as e:
            print(f"DEBUG: Error extracting log date range: {e}")
            return None
    
    def format_log_timestamp(self, timestamp_str):
        """Format a timestamp string to DD-MM-YYYY HH:MM:SS format"""
        try:
            from datetime import datetime
            
            # Try different parsing formats
            formats = [
                '%Y-%m-%d %H:%M:%S',    # YYYY-MM-DD HH:MM:SS
                '%m/%d/%Y %H:%M:%S',    # MM/DD/YYYY HH:MM:SS
                '%d-%m-%Y %H:%M:%S',    # DD-MM-YYYY HH:MM:SS
                '%Y%m%d_%H%M%S',        # YYYYMMDD_HHMMSS
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.strftime('%d-%m-%Y %H:%M:%S')
                except ValueError:
                    continue
            
            # If no format matches, return the original string
            return timestamp_str
            
        except Exception:
            return timestamp_str
    
    def get_analysis_data(self):
        """Get analysis data from current image classifications"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return {'no_code_count': 0, 'read_failure_count': 0, 'ocr_readable_count': 0, 'total_sessions': 0, 'actual_sessions': 0, 'total_entered': 0}
            
        # Calculate session labels
        session_labels_dict = self.calculate_session_labels()
        
        # Count sessions by category
        no_code_count = sum(1 for label in session_labels_dict.values() if label == "no label")
        read_failure_count = sum(1 for label in session_labels_dict.values() if label == "read failure")
        ocr_readable_count = self.calculate_sessions_with_ocr_readable()
        
        # Get actual sessions count (number of sessions found in images)
        actual_sessions = len(session_labels_dict)
        
        # Get total entered (expected total from user input)
        total_entered = int(self.total_sessions_var.get()) if self.total_sessions_var.get() else 0
        
        return {
            'no_code_count': no_code_count,
            'read_failure_count': read_failure_count,
            'ocr_readable_count': ocr_readable_count,
            'total_sessions': len(session_labels_dict),
            'actual_sessions': actual_sessions,
            'total_entered': total_entered
        }
    
    def calculate_gross_rate(self, log_results, analysis_data):
        """Calculate gross rate percentage"""
        unique_ids = log_results['unique_ids']
        total_noread = log_results.get('total_noread', 0)
        
        if unique_ids > 0:
            read_parcels = unique_ids - total_noread
            return (read_parcels / unique_ids) * 100
        return 0.0
    
    def calculate_net_reading_performance(self, log_results, analysis_data):
        """Calculate net reading performance percentage using the NEW formulas"""
        # Get the data from analysis_data which matches the Analysis tab calculations
        total_entered = analysis_data.get('total_entered', 0)
        actual_sessions = analysis_data.get('actual_sessions', 0)  
        sessions_read_failure = analysis_data.get('read_failure_count', 0)
        sessions_ocr_readable = analysis_data.get('ocr_readable_count', 0)
        
        # Use the NEW formulas:
        # Total readable w/o OCR = total entered - session number + read failure
        total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
        
        # Calculate OCR readable sessions that are NOT read failure sessions
        sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
        
        # Total readable w/ OCR = Total readable w/o OCR + OCR readable sessions that are not read failure
        total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
        
        results = {}
        
        # Net reading performance excluding OCR readable  
        if total_readable_excl_ocr > 0:
            successful_reads_excl_ocr = total_readable_excl_ocr - sessions_read_failure
            results['excl_ocr'] = (successful_reads_excl_ocr / total_readable_excl_ocr) * 100
            net_numerator_excl_ocr = successful_reads_excl_ocr
        else:
            results['excl_ocr'] = 0.0
            net_numerator_excl_ocr = 0
            
        # Net reading performance including OCR readable - use same logic as main stats
        if total_readable_incl_ocr > 0:
            # sessions read using OCR = sessions that were read using OCR, regardless of other status
            sessions_read_using_ocr = sessions_ocr_readable
            net_numerator_incl_ocr = net_numerator_excl_ocr + sessions_read_using_ocr
            results['incl_ocr'] = (net_numerator_incl_ocr / total_readable_incl_ocr) * 100
        else:
            results['incl_ocr'] = 0.0
            
        return results
    
    def export_log_analysis_report(self):
        """Export the log analysis results to a text report file"""
        if not hasattr(self, 'current_log_analysis') or not self.current_log_analysis:
            messagebox.showwarning("No Data", "No log analysis results available to export.")
            return
        
        try:
            from datetime import datetime
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Use the same directory as the selected folder if available
            if hasattr(self, 'folder_path') and self.folder_path:
                report_path = os.path.join(self.folder_path, f"FIS_Analytics_Report_{timestamp}.txt")
            else:
                report_path = f"FIS_Analytics_Report_{timestamp}.txt"
            
            # Get the current analysis data
            results = self.current_log_analysis
            log_date_info = self.extract_log_date_range()
            analysis_data = self.get_analysis_data()
            
            # Generate the report content
            report_lines = []
            report_lines.append("AURORA FIS ANALYTICS INTERNAL TOOL - LOG ANALYSIS REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
            report_lines.append("")
            
            # PATH section
            report_lines.append("=== PATH ===")
            if hasattr(self, 'folder_path') and self.folder_path:
                report_lines.append(f"Folder Path: {self.folder_path}")
            else:
                report_lines.append("Folder Path: No folder selected")
            
            report_lines.append("")
            
            # DATES section
            report_lines.append("=== DATES ===")
            if log_date_info:
                report_lines.append(f"Start Date: {log_date_info['start_date']}")
                report_lines.append(f"End Date: {log_date_info['end_date']}")
            else:
                report_lines.append("Start Date: Not available")
                report_lines.append("End Date: Not available")
            
            report_lines.append("")
            
            # LOG FILE ANALYSIS section
            report_lines.append("LOG FILE ANALYSIS")
            report_lines.append("-" * 20)
            report_lines.append(f"Number of sessions: {results['unique_ids']}")
            
            # Calculate read vs noread sessions
            total_noread = results.get('total_noread', 0)
            unique_ids = results['unique_ids']
            read_sessions = unique_ids - total_noread
            
            report_lines.append(f"Number of Read sessions: {read_sessions}")
            report_lines.append(f"Number of No-Read sessions: {total_noread}")
            report_lines.append(f"Number of False triggers: {results['false_triggers']}")
            report_lines.append(f"Number of Effective sessions: {results['effective_session_count']}")
            
            report_lines.append("")
            
            # READING ANALYSIS section
            report_lines.append("READING ANALYSIS")
            report_lines.append("-" * 16)
            
            # Calculate fail reading parcels (NOREAD minus missed triggers)
            fail_reading_parcels = total_noread - results['false_triggers']
            if fail_reading_parcels < 0:
                fail_reading_parcels = 0
                
            report_lines.append(f"Number of Failed sessions: {fail_reading_parcels}")
            report_lines.append(f"Number of No-Code sessions: {analysis_data['no_code_count']}")
            report_lines.append(f"Number of Read-Failure sessions: {analysis_data['read_failure_count']}")
            
            # Calculate total unreadable using same formula as Analysis tab
            # Use consistent formula: total_sessions - sessions_no_code - sessions_read_failure
            total_unreadable = len(self.calculate_session_labels()) - analysis_data['no_code_count'] - analysis_data['read_failure_count']
            if total_unreadable < 0:
                total_unreadable = 0
                
            report_lines.append(f"Number of Unreadable sessions: {total_unreadable}")
            
            report_lines.append("")
            
            # READ RATE section
            report_lines.append("=== READ RATE ===")
            
            # Calculate rates
            gross_rate = self.calculate_gross_rate(results, analysis_data)
            net_reading_performance = self.calculate_net_reading_performance(results, analysis_data)
            
            report_lines.append(f"Gross read performance: {gross_rate:.1f}%")
            report_lines.append(f"Net read performance (excl. OCR): {net_reading_performance['excl_ocr']:.2f}%")
            report_lines.append(f"Net read performance (incl. OCR): {net_reading_performance['incl_ocr']:.2f}%")
            
            # Add OCR improvement percentage
            if net_reading_performance['excl_ocr'] >= 0 and net_reading_performance['incl_ocr'] >= 0:
                # Get analysis data to calculate actual read numbers
                total_entered = analysis_data.get('total_entered', 0)
                actual_sessions = analysis_data.get('actual_sessions', 0)
                sessions_read_failure = analysis_data.get('read_failure_count', 0)
                sessions_ocr_readable = self.calculate_sessions_with_ocr_readable()
                sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
                
                # Calculate readable sessions and read images
                total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
                total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
                
                read_images_excl_ocr = total_readable_excl_ocr - sessions_read_failure
                read_images_incl_ocr = read_images_excl_ocr + sessions_ocr_readable
                
                if read_images_excl_ocr > 0:
                    # Formula: [(Read w/ OCR - Read w/o OCR) / Read w/o OCR] × 100
                    ocr_improvement = ((read_images_incl_ocr - read_images_excl_ocr) / read_images_excl_ocr) * 100
                    report_lines.append(f"OCR read rate improvement: +{ocr_improvement:.2f}%")
                else:
                    report_lines.append("OCR read rate improvement: N/A (no baseline reads)")
            
            report_lines.append("")
            report_lines.append("=" * 50)
            report_lines.append("End of Report")
            
            # Write the report file
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            # Show success message
            messagebox.showinfo("Export Successful", 
                              f"Log analysis report exported successfully!\n\n"
                              f"File: {os.path.basename(report_path)}\n"
                              f"Location: {os.path.dirname(report_path)}")
            
        except Exception as e:
            messagebox.showerror("Export Error", 
                               f"Failed to export log analysis report:\n\n{str(e)}")
    
    def enable_export_button(self):
        """Enable the export button when analysis results are available"""
        if hasattr(self, 'btn_export_log_report'):
            self.btn_export_log_report.config(state='normal')

    def generate_issues_csv(self, results):
        """Generate a CSV file with IDs for missed triggers and timeouts"""
        import csv
        from datetime import datetime
        
        # Create CSV filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use the same directory as the selected folder if available, otherwise use current directory
        if hasattr(self, 'folder_path') and self.folder_path:
            csv_path = os.path.join(self.folder_path, f"FIS_Analytics_Report_{timestamp}.csv")
        else:
            csv_path = f"FIS_Analytics_Report_{timestamp}.csv"
        
        try:
            # Combine missed triggers and timeouts into one list
            all_issues = []
            
            # Add missed triggers
            for id_val in results.get('missed_trigger_ids', []):
                all_issues.append((id_val, 'MissedTrig'))
            
            # Add timeouts
            for id_val in results.get('timeout_ids', []):
                all_issues.append((id_val, 'Timeout'))
            
            # Sort by ID (convert to int for proper numerical sorting)
            all_issues.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'))
            
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['ID', 'Issue_Type'])
                
                # Write data rows
                for id_val, issue_type in all_issues:
                    writer.writerow([id_val, issue_type])
            

            
        except Exception as e:
            # If CSV generation fails, show error in display
            self.log_results_text.config(state=tk.NORMAL)
            self.log_results_text.insert(tk.END, f"\n\n❌ Error generating CSV: {str(e)}")
            self.log_results_text.config(state=tk.DISABLED)

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
        elif filter_value == "OCR recovered only":
            # Special filter for OCR recovered images
            self.image_paths = [path for path in self.all_image_paths
                               if self.ocr_readable.get(path, False)]
        else:
            # Map filter names to label values
            filter_map = {
                "(Unclassified) only": "(Unclassified)",
                "no label only": "no label",
                "read failure only": "read failure",
                "incomplete only": "incomplete",
                "unreadable only": "unreadable"
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
        self.update_session_stats()
        self.update_total_stats()
        self.update_progress_display()
        
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
        """Helper method to load CSV file"""
        # max_session_index = 0  # Session index tracking removed
        
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Read header
            
            for row in reader:
                if len(row) >= 2:  # At minimum need image_path and image_label
                    stored_path = row[0]  # This might be relative or absolute
                    image_label = row[1]
                    
                    # Read OCR Readable status if available (3rd column, index 2)
                    ocr_readable = False
                    if len(row) >= 3:
                        try:
                            # Handle both boolean and string representations
                            ocr_value = row[2]
                            if isinstance(ocr_value, str):
                                ocr_readable = ocr_value.lower() in ('true', 't', '1', 'yes')
                            else:
                                ocr_readable = bool(ocr_value)
                        except (ValueError, TypeError):
                            ocr_readable = False  # Default to False if parsing fails
                    
                    # Read Comment if available (4th column, index 3)
                    comment = ""
                    if len(row) >= 4:
                        comment = row[3].strip()
                    
                    # Convert relative path back to absolute path if needed
                    if hasattr(self, 'folder_path') and self.folder_path:
                        if os.path.isabs(stored_path):
                            # Already absolute path (backward compatibility)
                            image_path = stored_path
                        else:
                            # Relative path - convert to absolute
                            image_path = os.path.join(self.folder_path, stored_path)
                            # Normalize the path to handle any inconsistencies
                            image_path = os.path.normpath(image_path)
                    else:
                        # No folder_path available, use as-is
                        image_path = stored_path
                    
                    self.labels[image_path] = image_label
                    self.ocr_readable[image_path] = ocr_readable
                    self.comments[image_path] = comment
                    
                    # Session index loading logic removed - no longer used
                    # if len(row) >= 8 and row[7]:  # session_index is now 8th column (index 7)
                    #     try:
                    #         session_index = int(row[7])
                    #         session_id = self.get_session_number(image_path)
                    #         if session_id:
                    #             self.session_indices[session_id] = session_index
                    #             max_session_index = max(max_session_index, session_index)
                    #     except (ValueError, TypeError):
                    #         pass  # Skip invalid session index values
        
        # Session index tracking removed
        # self.next_session_index = max_session_index + 1

    def save_csv(self):
        if not self.csv_filename:
            return
            
        try:
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['image_path', 'image_label', 'OCR_Readable', 'Comment', 'session_number', 'session_label', 'session_OCR_readable', 'session_index'])
                
                # Calculate current session labels
                session_labels_dict = self.calculate_session_labels()
                
                # Calculate session OCR readable status
                session_ocr_readable_dict = self.calculate_session_ocr_readable_status()
                
                for path, label in self.labels.items():
                    # Convert absolute path to relative path from the selected folder
                    if hasattr(self, 'folder_path') and self.folder_path:
                        try:
                            # Normalize both paths before calculating relative path
                            normalized_path = os.path.normpath(path)
                            normalized_folder = os.path.normpath(self.folder_path)
                            relative_path = os.path.relpath(normalized_path, normalized_folder)
                        except ValueError:
                            # If relpath fails (e.g., different drives), use just the filename
                            relative_path = os.path.basename(path)
                    else:
                        relative_path = os.path.basename(path)
                    
                    session_id = self.get_session_number(path)
                    session_label = session_labels_dict.get(session_id, "no label") if session_id else "no label"
                    session_ocr_readable = session_ocr_readable_dict.get(session_id, False) if session_id else False
                    # session_index functionality removed
                    ocr_readable = self.ocr_readable.get(path, False)
                    comment = self.comments.get(path, "")
                    writer.writerow([relative_path, label, ocr_readable, comment, session_id or "", session_label, session_ocr_readable, ""])
            
            # Also generate statistics CSV file
            self.save_stats_csv()
            
        except PermissionError as e:
            print(f"ERROR: Permission denied when saving CSV: {self.csv_filename}")
            print("Possible solutions:")
            print("1. Close Excel if the file is open")
            print("2. Check if OneDrive is syncing the folder")
            print("3. Try running as administrator")
            print("4. Choose a different folder location")
            # Show message to user
            try:
                messagebox.showerror("File Save Error", 
                    f"Cannot save file:\n{os.path.basename(self.csv_filename)}\n\n"
                    f"The file might be open in Excel or another program.\n"
                    f"Please close any programs using this file and try again.")
            except:
                pass
                
        except Exception as e:
            print(f"ERROR: Unexpected error saving CSV: {str(e)}")
            try:
                messagebox.showerror("File Save Error", 
                    f"Cannot save file:\n{os.path.basename(self.csv_filename)}\n\n"
                    f"Error: {str(e)}")
            except:
                pass

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
        
        try:
            with open(stats_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write statistics header
                writer.writerow(['category', 'metric', 'value', 'description'])
                
                # Write all statistics
                for category, metrics in stats_data.items():
                    for metric, data in metrics.items():
                        writer.writerow([category, metric, data['value'], data['description']])
            
            print(f"Stats CSV saved successfully: {stats_filename}")
            
        except PermissionError as e:
            print(f"ERROR: Permission denied when saving stats CSV: {stats_filename}")
            print("Possible solutions:")
            print("1. Close Excel if the file is open")
            print("2. Check if OneDrive is syncing the folder")
            print("3. Try running as administrator")
            print("4. Choose a different folder location")
            # Try to show a message box to the user
            try:
                messagebox.showerror("File Save Error", 
                    f"Cannot save stats file:\n{os.path.basename(stats_filename)}\n\n"
                    f"The file might be open in Excel or another program.\n"
                    f"Please close any programs using this file and try again.")
            except:
                pass  # If messagebox fails, just continue
                
        except Exception as e:
            print(f"ERROR: Unexpected error saving stats CSV: {str(e)}")
            try:
                messagebox.showerror("File Save Error", 
                    f"Cannot save stats file:\n{os.path.basename(stats_filename)}\n\n"
                    f"Error: {str(e)}")
            except:
                pass

    def calculate_comprehensive_stats(self):
        """Calculate comprehensive statistics for the stats CSV"""
        stats = {
            'Image_Counts': {},
            'Session_Counts': {},
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
        
        # Calculate session statistics
        session_labels_dict = self.calculate_session_labels()
        session_counts = {}
        unique_sessions = set()
        
        for path in self.all_image_paths if hasattr(self, 'all_image_paths') else []:
            session_id = self.get_session_number(path)
            if session_id:
                unique_sessions.add(session_id)
                session_label = session_labels_dict.get(session_id, "no label")
                session_counts[session_label] = session_counts.get(session_label, 0) + 1
        
        # Store session statistics
        for label, count in session_counts.items():
            stats['Session_Counts'][f'sessions_{label}'] = {
                'value': count,
                'description': f'Number of sessions classified as {label}'
            }
        
        stats['Session_Counts']['total_unique_sessions'] = {
            'value': len(unique_sessions),
            'description': 'Total number of unique sessions'
        }
        
        # Add total number of sessions (including duplicates/all session entries)
        total_session_entries = 0
        for path in self.all_image_paths if hasattr(self, 'all_image_paths') else []:
            if self.get_session_number(path):
                total_session_entries += 1
        
        stats['Session_Counts']['total_session_entries'] = {
            'value': total_session_entries,
            'description': 'Total number of session entries (including duplicates)'
        }
        
        # Add manually entered total number of sessions
        try:
            manual_total_sessions = int(self.total_sessions_var.get()) if hasattr(self, 'total_sessions_var') and self.total_sessions_var.get() else 0
        except ValueError:
            manual_total_sessions = 0
            
        stats['Session_Counts']['manual_total_sessions'] = {
            'value': manual_total_sessions,
            'description': 'Manually entered total number of sessions'
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
        charts_window.title(f"Statistics Charts - Aurora FIS Analytics INTERNAL tool v{VERSION}")
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
        
        # Calculate session statistics
        session_labels_dict = self.calculate_session_labels()
        
        if not session_labels_dict:
            # Show message if no session data
            label = tk.Label(parent_frame, text="📦 No session data available\nPlease classify some images first.",
                           font=("Arial", 14), bg="#FAFAFA", fg="#666666")
            label.pack(expand=True)
            return
        
        # Count sessions by label
        session_counts = {}
        for session_label in session_labels_dict.values():
            session_counts[session_label] = session_counts.get(session_label, 0) + 1
        
        # Prepare data for pie chart
        labels = list(session_counts.keys())
        sizes = list(session_counts.values())
        
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
        
        # 2. Read Rate Bars (if total sessions is set)
        try:
            total_entered = int(self.total_sessions_var.get()) if self.total_sessions_var.get() else 0
            if total_entered > 0:
                session_labels_dict = self.calculate_session_labels()
                actual_sessions = len(session_labels_dict)
                
                sessions_no_code = sum(1 for label in session_labels_dict.values() if label == "no label")
                sessions_read_failure = sum(1 for label in session_labels_dict.values() if label == "read failure")
                sessions_ocr_readable = self.calculate_sessions_with_ocr_readable()
                
                # Use NEW formulas for total readable calculation
                total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
                sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
                total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
                
                # Calculate rates
                gross_rate = ((total_entered - actual_sessions) / total_entered * 100) if total_entered > 0 else 0
                net_rate = ((total_readable_incl_ocr - sessions_read_failure) / total_readable_incl_ocr * 100) if total_readable_incl_ocr > 0 else 0
                
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
        
        # Add OCR readable count as separate line
        if hasattr(self, 'all_image_paths') and self.all_image_paths:
            ocr_readable_count = len([path for path in self.all_image_paths if self.ocr_readable.get(path, False)])
            lines.append(f"  OCR recovered: {ocr_readable_count}")
        
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
    
    # Session index display method removed - no longer used
    # def update_session_index_display(self):
    #     """Update the session index display for current image."""
    #     if not self.image_paths:
    #         self.session_index_var.set("")
    #         return
    #     
    #     current_path = self.image_paths[self.current_index]
    #     session_index = self.get_session_index(current_path)
    #     
    #     if session_index is not None:
    #         self.session_index_var.set(f"Session Index: {session_index}")
    #     else:
    #         self.session_index_var.set("Session Index: None")

    def get_session_number(self, image_path):
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

    def calculate_session_labels(self):
        """Calculate session labels based on the labeling rules and return a dict"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return {}

        # Group images by their unique identifier (ID + Timestamp combination)
        sessions = {}
        for path in self.all_image_paths:
            session_id = self.get_session_number(path)
            if session_id:
                if session_id not in sessions:
                    sessions[session_id] = []
                sessions[session_id].append(path)

        # Calculate session labels based on rules with new 7-category system
        session_labels_dict = {}
        
        for session_id, session_paths in sessions.items():
            session_image_labels = [self.labels.get(path, LABELS[0]) for path in session_paths]
            
            # Only include sessions that have at least one classified image
            classified_labels = [label for label in session_image_labels if label != "(Unclassified)"]
            
            if not classified_labels:
                # Skip sessions with no classified images
                continue
            
            # Apply session labeling rules in priority order:
            # 1. If any image has "read failure", session is "read failure" (technical issue)
            if "read failure" in classified_labels:
                session_labels_dict[session_id] = "read failure"
            # 2. If any image has "unreadable" issues, session has "unreadable" issues
            elif "unreadable" in classified_labels:
                session_labels_dict[session_id] = "unreadable"
            # 3. If any image is "incomplete", session is "incomplete"
            elif "incomplete" in classified_labels:
                session_labels_dict[session_id] = "incomplete"
            # 4. If ALL classified images are "no label", session is "no label"
            elif all(label == "no label" for label in classified_labels):
                session_labels_dict[session_id] = "no label"
            # 5. Default: if mix of categories, session is "incomplete"
            else:
                session_labels_dict[session_id] = "incomplete"
                
        return session_labels_dict

    def calculate_sessions_with_ocr_readable(self):
        """Calculate number of sessions that have at least one OCR readable image"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return 0
        
        # Group images by session
        sessions = {}
        for path in self.all_image_paths:
            session_id = self.get_session_number(path)
            if session_id:
                if session_id not in sessions:
                    sessions[session_id] = []
                sessions[session_id].append(path)
        
        # Count sessions with at least one OCR readable image
        ocr_readable_sessions = 0
        for session_id, session_paths in sessions.items():
            for path in session_paths:
                if self.ocr_readable.get(path, False):
                    ocr_readable_sessions += 1
                    break  # Found one OCR readable image in this session, move to next session
        
        return ocr_readable_sessions

    def calculate_session_ocr_readable_status(self):
        """Calculate OCR readable status for each session (True if at least one image in session is OCR readable)"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return {}
        
        # Group images by session
        sessions = {}
        for path in self.all_image_paths:
            session_id = self.get_session_number(path)
            if session_id:
                if session_id not in sessions:
                    sessions[session_id] = []
                sessions[session_id].append(path)
        
        # Calculate OCR readable status for each session
        session_ocr_readable_dict = {}
        for session_id, session_paths in sessions.items():
            # Check if any image in this session is OCR readable
            has_ocr_readable = any(self.ocr_readable.get(path, False) for path in session_paths)
            session_ocr_readable_dict[session_id] = has_ocr_readable
        
        return session_ocr_readable_dict

    def calculate_ocr_readable_non_failure_sessions(self):
        """Calculate number of sessions that have OCR readable images but are NOT classified as read failure"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return 0
        
        session_labels_dict = self.calculate_session_labels()
        session_ocr_readable_dict = self.calculate_session_ocr_readable_status()
        
        # Count sessions that are OCR readable but not read failure
        count = 0
        for session_id, is_ocr_readable in session_ocr_readable_dict.items():
            if is_ocr_readable:  # Session has OCR readable images
                session_label = session_labels_dict.get(session_id, "no label")
                if session_label != "read failure":  # And is not classified as read failure
                    count += 1
        
        return count

    def update_session_stats(self):
        """Calculate session statistics based on the labeling rules"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            self.session_count_var.set("")
            return

        session_labels_dict = self.calculate_session_labels()
        
        # Count sessions by different categories
        total_sessions = len(session_labels_dict)
        sessions_no_code = 0
        sessions_read_failure = 0
        sessions_ocr_readable = 0
        
        for session_label in session_labels_dict.values():
            if session_label == "no label":
                sessions_no_code += 1
            elif session_label == "read failure":
                sessions_read_failure += 1
        
        # Calculate sessions with OCR readable images (separate from primary classification)
        sessions_ocr_readable = self.calculate_sessions_with_ocr_readable()
        
        # Calculate sessions with unreadable code (excluding no_code and read_failure)
        sessions_unreadable_code = total_sessions - sessions_no_code - sessions_read_failure
        
        # Calculate total readable sessions using expected total from text field
        try:
            total_entered = int(self.total_sessions_var.get()) if self.total_sessions_var.get() else 0
            # Use NEW formulas:
            # Total readable w/o OCR = total entered - actual sessions + read failure  
            total_readable_excl_ocr = total_entered - total_sessions + sessions_read_failure
            # Calculate OCR readable sessions that are NOT read failure sessions
            sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
            # Total readable w/ OCR = Total readable w/o OCR + OCR readable sessions that are not read failure
            total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
        except ValueError:
            total_readable_excl_ocr = "N/A (Enter expected total)"
            total_readable_incl_ocr = "N/A (Enter expected total)"
        
        # Format the display
        lines = [
            f"Number of failed sessions: {total_sessions}",
            f"Sessions with no label: {sessions_no_code}",
            f"Sessions with read failure: {sessions_read_failure}",
            f"Sessions with unreadable code: {sessions_unreadable_code}",
            f"Sessions recovered with OCR: {sessions_ocr_readable}",
            f"Total readable sessions (excl. OCR): {total_readable_excl_ocr}",
            f"Total readable sessions (incl. OCR): {total_readable_incl_ocr}"
        ]
        
        self.session_count_var.set("\n".join(lines))

    def update_total_stats(self):
        """Calculate statistics against manually entered total number of sessions"""
        try:
            total_entered = int(self.total_sessions_var.get()) if self.total_sessions_var.get() else 0
        except ValueError:
            self.session_stats_var.set("")
            return

        if total_entered <= 0:
            self.session_stats_var.set("")
            return

        # Get current session statistics
        session_labels_dict = self.calculate_session_labels()
        actual_sessions = len(session_labels_dict)
        
        sessions_no_code = 0
        sessions_read_failure = 0
        
        for session_label in session_labels_dict.values():
            if session_label == "no label":
                sessions_no_code += 1
            elif session_label == "read failure":
                sessions_read_failure += 1
        
        # Calculate OCR readable sessions
        sessions_ocr_readable = self.calculate_sessions_with_ocr_readable()
        sessions_ocr_readable_non_failure = self.calculate_ocr_readable_non_failure_sessions()
        
        # Calculate readable sessions using NEW formulas:
        # Total readable w/o OCR = total entered - session number + read failure
        total_readable_excl_ocr = total_entered - actual_sessions + sessions_read_failure
        # Total readable w/ OCR = Total readable w/o OCR + OCR readable sessions that are not read failure
        total_readable_incl_ocr = total_readable_excl_ocr + sessions_ocr_readable_non_failure
        
        lines = []
        
        # Gross read rate: (Total number of sessions) minus (Number of sessions) out of (Total number of sessions)
        if total_entered > 0:
            gross_numerator = total_entered - actual_sessions
            gross_read_rate = (gross_numerator / total_entered) * 100
            lines.append(f"Gross read rate: {gross_numerator}/{total_entered} ({gross_read_rate:.2f}%)")
        
        # Net read rate: (Total number of readable sessions) minus (Sessions with read failure) out of (Total number of readable sessions)
        
        # Calculate net numerator excluding OCR (always calculate for use in incl OCR calculation)
        net_numerator_excl_ocr = total_readable_excl_ocr - sessions_read_failure
        
        if total_readable_excl_ocr > 0:
            # Show net read rate excluding OCR readable sessions
            net_read_rate_excl_ocr = (net_numerator_excl_ocr / total_readable_excl_ocr) * 100
            lines.append(f"Net read rate (excl. OCR): {net_numerator_excl_ocr}/{total_readable_excl_ocr} ({net_read_rate_excl_ocr:.2f}%)")
        else:
            lines.append("Net read rate (excl. OCR): N/A (no readable sessions)")
        
        # Show net read rate including OCR readable sessions
        if total_readable_incl_ocr > 0:
            # sessions read using OCR = sessions that were read using OCR, regardless of other status
            sessions_read_using_ocr = sessions_ocr_readable
            net_numerator_incl_ocr = net_numerator_excl_ocr + sessions_read_using_ocr
            net_read_rate_incl_ocr = (net_numerator_incl_ocr / total_readable_incl_ocr) * 100
            lines.append(f"Net read rate (incl. OCR): {net_numerator_incl_ocr}/{total_readable_incl_ocr} ({net_read_rate_incl_ocr:.2f}%)")
        else:
            lines.append("Net read rate (incl. OCR): N/A (no readable sessions)")
        
        # Calculate and show OCR improvement percentage
        if total_readable_excl_ocr > 0 and total_readable_incl_ocr > 0:
            # Calculate number of read images (successful reads)
            read_images_excl_ocr = total_readable_excl_ocr - sessions_read_failure
            read_images_incl_ocr = read_images_excl_ocr + sessions_ocr_readable
            
            if read_images_excl_ocr > 0:
                # Formula: [(Read w/ OCR - Read w/o OCR) / Read w/o OCR] × 100
                ocr_improvement_percentage = ((read_images_incl_ocr - read_images_excl_ocr) / read_images_excl_ocr) * 100
                lines.append(f"OCR read rate improvement: +{ocr_improvement_percentage:.2f}%")
            else:
                lines.append("OCR read rate improvement: N/A (no baseline reads)")
        
        
        self.session_stats_var.set("\n".join(lines))

    def auto_detect_total_groups(self):
        """Auto-detect total number of sessions by finding the range between min and max ID values from filenames"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return
        
        max_id = 0
        min_id = float('inf')
        valid_ids_found = False
        
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
                    min_id = min(min_id, id_number)
                    valid_ids_found = True
                except ValueError:
                    # Skip files where the first part is not a number
                    continue
        
        if valid_ids_found and max_id >= min_id:
            # Calculate total sessions as the range: max_id - min_id + 1
            total_sessions = max_id - min_id + 1
            print(f"DEBUG: Auto-detected sessions range: {min_id} to {max_id} = {total_sessions} total sessions")
            
            # Set the total sessions field with the calculated range
            self.total_sessions_var.set(str(total_sessions))
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

    def apply_histogram_equalization(self, img):
        """Apply histogram equalization to enhance image contrast"""
        try:
            # Convert PIL image to numpy array for OpenCV processing
            import numpy as np
            
            # Convert to RGB if not already (PIL images are RGB by default)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert PIL image to numpy array
            img_array = np.array(img)
            
            # Convert RGB to BGR for OpenCV (OpenCV uses BGR)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale for histogram equalization
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization
            equalized = cv2.equalizeHist(gray)
            
            # Convert back to BGR color by replicating the equalized grayscale to all channels
            # This creates a grayscale image with better contrast
            equalized_bgr = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
            
            # For color images, apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to each channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            
            # Split BGR channels and apply CLAHE to each
            b, g, r = cv2.split(img_bgr)
            b_eq = clahe.apply(b)
            g_eq = clahe.apply(g)
            r_eq = clahe.apply(r)
            
            # Merge channels back
            equalized_color = cv2.merge([b_eq, g_eq, r_eq])
            
            # Convert back to RGB for PIL
            equalized_rgb = cv2.cvtColor(equalized_color, cv2.COLOR_BGR2RGB)
            
            # Convert numpy array back to PIL image
            equalized_img = Image.fromarray(equalized_rgb)
            
            return equalized_img
            
        except Exception as e:
            # If histogram equalization fails, return original image
            print(f"Histogram equalization failed: {e}")
            return img

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
                label = "no label"  # No barcode detected
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
            if not hasattr(self, 'comments'):
                self.comments = {}
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
            self.root.after(0, self.update_session_stats)
            
            # Small delay to show progress (and simulate processing time)
            time.sleep(0.1)
            
            processed += 1
        
        # Log session summary
        self.logger.info("-" * 30)
        self.logger.info("AUTO-CLASSIFICATION SUMMARY:")
        self.logger.info(f"Total processed: {total_images}")
        self.logger.info(f"Classified as 'no label': {no_code_count}")
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
        self.update_session_stats()
        
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
                label = "no label"  # No barcode detected
                no_code_count += 1
            else:  # detection_result > 0
                label = "read failure"  # Barcode detected but not readable
                read_failure_count += 1
            
            # Log the classification decision
            self.logger.info(f"NEW FILE CLASSIFIED: {filename} → {label} (barcode count: {detection_result})")
            
            # Update labels dictionary
            if not hasattr(self, 'labels'):
                self.labels = {}
            if not hasattr(self, 'comments'):
                self.comments = {}
            self.labels[file_path] = label
            
            # Save to CSV and update stats
            self.root.after(0, self.save_csv)
            self.root.after(0, self.update_counts)
            self.root.after(0, self.update_total_stats)
            self.root.after(0, self.update_session_stats)
            
            # Small delay to show progress
            time.sleep(0.1)
            processed += 1
        
        # Log session summary
        self.logger.info("-" * 30)
        self.logger.info("NEW FILES AUTO-CLASSIFICATION SUMMARY:")
        self.logger.info(f"Total new files processed: {total_files}")
        self.logger.info(f"Classified as 'no label': {no_code_count}")
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
            "no label only": ("no label", "no_label"),
            "read failure only": ("read failure", "read_failure"),
            "incomplete only": ("incomplete", "incomplete"),
            "unreadable only": ("unreadable", "unreadable")
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

    def generate_sessions_csv(self):
        """Generate CSV files containing unique session IDs grouped by classification category"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            messagebox.showwarning("No Images", "Please select a folder with images first.")
            return
        
        # Dictionary to store session IDs by category
        sessions_by_category = {
            'no label': set(),
            'read failure': set(),
            'incomplete': set(),
            'unreadable': set(),
            'unlabeled': set()  # For images without any classification
        }
        
        # Progress setup
        self.btn_gen_sessions_csv.config(state='disabled', text="Generating...")
        self.auto_detect_progress_var.set("Extracting session IDs by category...")
        
        # Collect session IDs from all images, grouped by classification
        for i, image_path in enumerate(self.all_image_paths):
            filename = os.path.basename(image_path)
            
            # Update progress periodically
            if i % 100 == 0:
                progress_text = f"Processing {i+1}/{len(self.all_image_paths)} images..."
                self.auto_detect_progress_var.set(progress_text)
                self.root.update_idletasks()
            
            # Extract session ID from filename
            session_id = self.extract_session_id_from_filename(filename)
            if session_id:
                # Get the classification for this image
                classification = self.labels.get(image_path, 'unlabeled')
                
                # Add session ID to appropriate category
                if classification in sessions_by_category:
                    sessions_by_category[classification].add(session_id)
                else:
                    sessions_by_category['unlabeled'].add(session_id)
        
        try:
            # Create timestamp for consistent file naming
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            created_files = []
            total_sessions = 0
            
            # Generate CSV file for each category that has sessions
            for category, session_ids in sessions_by_category.items():
                if session_ids:  # Only create CSV if there are sessions in this category
                    # Sort session IDs for consistent output
                    sorted_session_ids = sorted(session_ids)
                    
                    # Create category-specific filename
                    safe_category = category.replace(' ', '_').replace('/', '_')
                    csv_filename = f"sessions_{safe_category}_{timestamp}.csv"
                    csv_path = os.path.join(self.folder_path, csv_filename)
                    
                    # Write CSV
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['session_id', 'category'])  # Header with category info
                        for session_id in sorted_session_ids:
                            writer.writerow([session_id, category])
                    
                    created_files.append((csv_filename, len(sorted_session_ids), category))
                    total_sessions += len(sorted_session_ids)
            
            # Also create a combined summary file
            summary_filename = f"sessions_summary_{timestamp}.csv"
            summary_path = os.path.join(self.folder_path, summary_filename)
            
            with open(summary_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['category', 'unique_sessions', 'filename'])  # Summary header
                for filename, session_count, category in created_files:
                    writer.writerow([category, session_count, filename])
            
            created_files.append((summary_filename, len(created_files), 'summary'))
            
            # Completion
            files_list = '\n'.join([f"• {filename} ({count} sessions)" for filename, count, _ in created_files])
            self.auto_detect_progress_var.set(f"Generated {len(created_files)} CSV files")
            self.btn_gen_sessions_csv.config(state='normal', text="Gen Sessions CSV")
            
            messagebox.showinfo("CSV Files Generated", 
                              f"Successfully generated {len(created_files)} CSV files:\n\n{files_list}\n\nTotal unique sessions processed: {total_sessions}")
            
        except Exception as e:
            self.btn_gen_sessions_csv.config(state='normal', text="Gen Sessions CSV")
            self.auto_detect_progress_var.set("CSV generation failed!")
            messagebox.showerror("CSV Error", f"Failed to generate sessions CSV:\n{str(e)}")

    def extract_session_id_from_filename(self, filename):
        """Extract session ID from filename based on known patterns"""
        # Remove file extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Common patterns for session ID extraction
        # Pattern 1: SessionID_TriggerID_... (e.g., "12345_001_image.jpg" -> session "12345")
        # Pattern 2: Complex patterns like "12345_001_20240101_120000.jpg"
        
        parts = name_without_ext.split('_')
        
        if len(parts) >= 2:
            # First part is typically the session ID
            potential_session_id = parts[0]
            
            # Validate that it looks like a session ID (numeric or alphanumeric)
            if potential_session_id and (potential_session_id.isdigit() or potential_session_id.isalnum()):
                return potential_session_id
        
        # If standard pattern doesn't work, try other common patterns
        # Some files might have format like "IMG_sessionID_triggerID.jpg"
        if filename.upper().startswith('IMG_') and len(parts) >= 3:
            return parts[1]  # Second part after IMG_
        
        # Fallback: return first part if it seems valid
        if parts and parts[0] and (parts[0].isdigit() or parts[0].isalnum()):
            return parts[0]
        
        return None

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
            
            current_image_paths.sort(key=self.get_image_sort_key)
            
            # Find new images (not in self.all_image_paths)
            new_images = []
            if hasattr(self, 'all_image_paths'):
                new_images = [path for path in current_image_paths if path not in self.all_image_paths]
                
                # Update the all_image_paths list with new images
                if new_images:
                    self.all_image_paths.extend(new_images)
                    self.all_image_paths.sort(key=self.get_image_sort_key)
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
                label = "no label"
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
            if not hasattr(self, 'comments'):
                self.comments = {}
            self.labels[image_path] = label
            
            # If this is the currently displayed image, refresh the display immediately
            if (hasattr(self, 'image_paths') and self.image_paths and 
                self.current_index < len(self.image_paths) and 
                image_path == self.image_paths[self.current_index]):
                self.show_image()
        
        # Save to CSV and update statistics
        self.save_csv()
        self.update_total_stats()
        self.update_session_stats()
        self.update_progress_display()
        self.update_counts()
        
        # Log session summary
        completion_time = datetime.now().strftime("%H:%M:%S")
        self.logger.info("-" * 30)
        self.logger.info("AUTO-CLASSIFICATION (TIMER) SUMMARY:")
        self.logger.info(f"Total processed: {total_images}")
        self.logger.info(f"Classified as 'no label': {no_code_count}")
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
