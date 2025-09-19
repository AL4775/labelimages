import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import re
import random
import threading
import time
import cv2
import numpy as np
import logging

LABELS = ["(Unclassified)", "no code", "read failure", "occluded", "image quality", "damaged", "other"]

class ImageLabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Label Tool")
        self.root.configure(bg="#FAFAFA")  # Very light gray background
        self.root.minsize(1600, 900)  # Set minimum window size - increased for wider radio button layout
        self.root.geometry("1800x950")  # Set initial window size - wider to accommodate all 7 label categories
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
        main_frame = tk.Frame(self.root, bg="#FAFAFA", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Folder selection and total parcels
        top_frame = tk.Frame(main_frame, bg="#FAFAFA")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Folder selection
        self.btn_select = tk.Button(top_frame, text="Select Folder", command=self.select_folder,
                                  bg="#A5D6A7", fg="white", font=("Arial", 12, "bold"),
                                  padx=20, pady=8, relief="flat")
        self.btn_select.pack(side=tk.LEFT)
        
        # Total number of parcels input (right side)
        total_frame = tk.Frame(top_frame, bg="#FAFAFA")
        total_frame.pack(side=tk.RIGHT)
        tk.Label(total_frame, text="Total number of parcels:", bg="#FAFAFA", font=("Arial", 10)).pack(side=tk.LEFT)
        self.total_parcels_var = tk.StringVar()
        self.total_parcels_entry = tk.Entry(total_frame, textvariable=self.total_parcels_var, width=10,
                                          font=("Arial", 10), bg="white", relief="solid", bd=1)
        self.total_parcels_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.total_parcels_entry.bind('<KeyRelease>', self.on_total_changed)
        
        # Filter dropdown (center)
        filter_frame = tk.Frame(top_frame, bg="#FAFAFA")
        filter_frame.pack(side=tk.LEFT, padx=(20, 0))
        tk.Label(filter_frame, text="Filter:", bg="#FAFAFA", font=("Arial", 10)).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All images")
        filter_options = ["All images", "(Unclassified) only", "no code only", "read failure only", "occluded only", "image quality only", "damaged only", "other only"]
        self.filter_menu = tk.OptionMenu(filter_frame, self.filter_var, *filter_options, command=self.on_filter_changed)
        self.filter_menu.config(bg="#F5F5F5", font=("Arial", 10), relief="solid", bd=1)
        self.filter_menu.pack(side=tk.LEFT, padx=(5, 0))

        # Main content area - horizontal layout
        content_frame = tk.Frame(main_frame, bg="#FAFAFA")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Left panel for controls
        left_panel = tk.Frame(content_frame, bg="#FAFAFA", width=220)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)  # Maintain fixed width
        
        # Center panel for image
        center_panel = tk.Frame(content_frame, bg="#FAFAFA")
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right panel for statistics
        right_panel = tk.Frame(content_frame, bg="#FAFAFA", width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)  # Maintain fixed width

        # === LEFT PANEL: Scale and Zoom Controls ===
        tk.Label(left_panel, text="View Controls", bg="#FAFAFA", font=("Arial", 11, "bold"), fg="#424242").pack(pady=(0, 10))
        
        # Scale info
        self.scale_info_var = tk.StringVar()
        self.scale_info_label = tk.Label(left_panel, textvariable=self.scale_info_var, 
                                       bg="#FAFAFA", font=("Arial", 9), fg="#757575",
                                       wraplength=180, justify=tk.LEFT)
        self.scale_info_label.pack(pady=(0, 5))
        
        # 1:1 Scale button
        self.btn_1to1 = tk.Button(left_panel, text="1:1 Scale", command=self.toggle_1to1_scale,
                                bg="#FFCC80", fg="white", font=("Arial", 10, "bold"),
                                padx=10, pady=5, relief="flat", width=12)
        self.btn_1to1.pack(pady=(0, 10))
        
        # Zoom controls
        zoom_frame = tk.Frame(left_panel, bg="#FAFAFA")
        zoom_frame.pack(pady=(0, 20))
        tk.Label(zoom_frame, text="Zoom:", bg="#FAFAFA", font=("Arial", 10)).pack()
        zoom_buttons = tk.Frame(zoom_frame, bg="#FAFAFA")
        zoom_buttons.pack(pady=(5, 0))
        
        self.btn_zoom_out = tk.Button(zoom_buttons, text="−", command=self.zoom_out,
                                    bg="#CE93D8", fg="white", font=("Arial", 12, "bold"),
                                    padx=8, pady=2, relief="flat", width=3)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=(0, 5))
        
        self.btn_zoom_in = tk.Button(zoom_buttons, text="+", command=self.zoom_in,
                                   bg="#CE93D8", fg="white", font=("Arial", 12, "bold"),
                                   padx=8, pady=2, relief="flat", width=3)
        self.btn_zoom_in.pack(side=tk.LEFT)

        # Export operations section
        export_frame = tk.Frame(left_panel, bg="#FAFAFA")
        export_frame.pack(pady=(0, 20))
        tk.Label(export_frame, text="Export:", bg="#FAFAFA", font=("Arial", 10, "bold")).pack()
        
        self.btn_gen_no_read = tk.Button(export_frame, text="Gen Read Failure\nFolder", 
                                       command=self.generate_read_failure_folder,
                                       bg="#9C27B0", fg="white", font=("Arial", 9, "bold"),
                                       padx=8, pady=5, relief="flat", width=12)
        self.btn_gen_no_read.pack(pady=(5, 0))

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
        
        # Add file status above label buttons
        self.status_var = tk.StringVar()
        self.status = tk.Label(center_panel, textvariable=self.status_var, bg="#FAFAFA", 
                             font=("Arial", 10), fg="#424242")
        self.status.pack(pady=(10, 5))
        
        # Add parcel index display
        self.parcel_index_var = tk.StringVar()
        self.parcel_index_label = tk.Label(center_panel, textvariable=self.parcel_index_var, bg="#FAFAFA",
                                         font=("Arial", 10), fg="#424242")
        self.parcel_index_label.pack(pady=(0, 5))

        # Navigation and radio buttons for labels (below image)
        self.label_var = tk.StringVar(value=LABELS[0])
        
        # Main container for navigation and labels
        nav_label_container = tk.Frame(center_panel, bg="#FAFAFA")
        nav_label_container.pack(pady=(0, 10))
        
        # Previous button (left side)
        self.btn_prev = tk.Button(nav_label_container, text="<< Prev", command=self.prev_image,
                                bg="#90CAF9", fg="white", font=("Arial", 10, "bold"),
                                padx=15, pady=8, relief="flat")
        self.btn_prev.pack(side=tk.LEFT, padx=(0, 15))
        
        # Label frame (center)
        label_frame = tk.Frame(nav_label_container, bg="#FAFAFA", relief="solid", bd=1, padx=15, pady=10)
        label_frame.pack(side=tk.LEFT)
        
        tk.Label(label_frame, text="Label:", bg="#FAFAFA", font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        # Add keyboard shortcut help
        help_text = tk.Label(label_frame, text="Keyboard shortcuts: Q, W, E, R, T, Y | O, P Navigate", 
                           bg="#FAFAFA", font=("Arial", 8), fg="#757575")
        help_text.pack(pady=(0, 5))
        
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
        for i, label in enumerate(LABELS):
            display_text = label + label_shortcuts[label]
            rb = tk.Radiobutton(radio_container, text=display_text, variable=self.label_var, 
                              value=label, command=self.set_label_radio,
                              bg=label_colors[label], font=("Arial", 10, "bold"),
                              selectcolor="white", padx=10, pady=5)
            rb.grid(row=0, column=i, padx=5)
            self.radio_buttons.append(rb)
        
        # Next button (right side)
        self.btn_next = tk.Button(nav_label_container, text="Next >>", command=self.next_image,
                                bg="#90CAF9", fg="white", font=("Arial", 10, "bold"),
                                padx=15, pady=8, relief="flat")
        self.btn_next.pack(side=tk.RIGHT, padx=(15, 0))
        
        # Jump to Next Unclassified button (right side)
        self.btn_jump_unclassified = tk.Button(nav_label_container, text="Jump to Next Unclassified", 
                                              command=self.jump_to_next_unclassified,
                                              bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
                                              padx=15, pady=8, relief="flat")
        self.btn_jump_unclassified.pack(side=tk.RIGHT, padx=(15, 0))

        # === RIGHT PANEL: Statistics ===
        tk.Label(right_panel, text="Statistics", bg="#FAFAFA", font=("Arial", 11, "bold"), fg="#424242").pack(pady=(0, 15))
        
        # Progress section
        progress_section = tk.Frame(right_panel, bg="#F5F5F5", relief="solid", bd=1, padx=10, pady=10)
        progress_section.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(progress_section, text="Progress", bg="#F5F5F5", font=("Arial", 10, "bold"), fg="#5E88D8").pack()
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(progress_section, textvariable=self.progress_var, bg="#F5F5F5",
                                     font=("Arial", 9), fg="#424242", wraplength=220)
        self.progress_label.pack(pady=(5, 0))
        
        # Image counts section
        counts_section = tk.Frame(right_panel, bg="#F5F5F5", relief="solid", bd=1, padx=10, pady=10)
        counts_section.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(counts_section, text="Image Counts", bg="#F5F5F5", font=("Arial", 10, "bold"), fg="#81C784").pack()
        self.count_var = tk.StringVar()
        self.count_label = tk.Label(counts_section, textvariable=self.count_var, bg="#F5F5F5",
                                  font=("Arial", 9), fg="#424242", wraplength=220)
        self.count_label.pack(pady=(5, 0))
        
        # Parcel statistics section
        parcel_section = tk.Frame(right_panel, bg="#F5F5F5", relief="solid", bd=1, padx=10, pady=10)
        parcel_section.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(parcel_section, text="Parcel count", bg="#F5F5F5", font=("Arial", 10, "bold"), fg="#81C784").pack()
        self.parcel_count_var = tk.StringVar()
        self.parcel_count_label = tk.Label(parcel_section, textvariable=self.parcel_count_var, 
                                         font=("Arial", 9), bg="#F5F5F5", fg="#424242", wraplength=220)
        self.parcel_count_label.pack(pady=(5, 0))
        
        # Total statistics section
        total_section = tk.Frame(right_panel, bg="#F5F5F5", relief="solid", bd=1, padx=10, pady=10)
        total_section.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(total_section, text="Net Stats", bg="#F5F5F5", font=("Arial", 10, "bold"), fg="#5E88D8").pack()
        self.parcel_stats_var = tk.StringVar()
        self.parcel_stats_label = tk.Label(total_section, textvariable=self.parcel_stats_var, 
                                         font=("Arial", 9), fg="#424242", bg="#F5F5F5", wraplength=220)
        self.parcel_stats_label.pack(pady=(5, 0))

        # Auto no-code / code classification section
        auto_detect_section = tk.Frame(right_panel, bg="#FFF3E0", relief="solid", bd=1, padx=10, pady=10)
        auto_detect_section.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(auto_detect_section, text="Auto detect new files", bg="#FFF3E0", font=("Arial", 10, "bold"), fg="#F57C00").pack()
        
        # Checkbox for auto barcode detection on new files
        self.auto_detect_enabled = tk.BooleanVar(value=False)
        self.auto_detect_checkbox = tk.Checkbutton(auto_detect_section, 
                                                 text="Auto detect barcodes on new files",
                                                 variable=self.auto_detect_enabled,
                                                 bg="#FFF3E0", font=("Arial", 9),
                                                 anchor="w", justify="left")
        self.auto_detect_checkbox.pack(pady=(10, 5), fill=tk.X)
        
        # Progress indicator for auto classification
        self.auto_detect_progress_var = tk.StringVar()
        self.auto_detect_progress_label = tk.Label(auto_detect_section, textvariable=self.auto_detect_progress_var,
                                                 bg="#FFF3E0", font=("Arial", 9), fg="#424242", wraplength=220)
        self.auto_detect_progress_label.pack()
        
        # Auto-timer controls
        timer_frame = tk.Frame(auto_detect_section, bg="#FFF3E0")
        timer_frame.pack(pady=(10, 0))
        
        self.auto_timer_enabled = tk.BooleanVar()
        self.auto_timer_button = tk.Button(timer_frame, text="Start", 
                                          command=self.toggle_auto_timer,
                                          bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                                          activebackground="#45a049", width=6)
        self.auto_timer_button.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(timer_frame, text="every", bg="#FFF3E0", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.auto_timer_interval = tk.StringVar(value="10")
        self.auto_timer_entry = tk.Entry(timer_frame, textvariable=self.auto_timer_interval,
                                        width=5, font=("Arial", 9), justify="center")
        self.auto_timer_entry.pack(side=tk.LEFT, padx=(0, 2))
        
        tk.Label(timer_frame, text="min", bg="#FFF3E0", font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Auto-timer status
        self.auto_timer_status_var = tk.StringVar()
        self.auto_timer_status_label = tk.Label(auto_detect_section, textvariable=self.auto_timer_status_var,
                                               bg="#FFF3E0", font=("Arial", 8), fg="#666666", wraplength=220)
        self.auto_timer_status_label.pack(pady=(5, 0))
        
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
        
        # Set focus to root window to capture keyboard events
        self.root.focus_set()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
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
        
        # Get canvas dimensions
        canvas_width = max(400, self.canvas.winfo_width())
        canvas_height = max(300, self.canvas.winfo_height())
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 400, 400
        
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

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
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
            self.apply_filter()
            # Try to find the image we were just on, or go to first if not found
            if current_path in self.image_paths:
                self.current_index = self.image_paths.index(current_path)
            else:
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
            self.label_var.set("no code")
            self.set_label_radio()
            self.jump_to_next_unclassified()

    def label_shortcut_w(self, event=None):
        """Keyboard shortcut: W for 'read failure'"""
        if self.image_paths:
            self.label_var.set("read failure")
            self.set_label_radio()
            self.jump_to_next_unclassified()

    def label_shortcut_e(self, event=None):
        """Keyboard shortcut: E for 'occluded'"""
        if self.image_paths:
            self.label_var.set("occluded")
            self.set_label_radio()
            self.jump_to_next_unclassified()

    def label_shortcut_r(self, event=None):
        """Keyboard shortcut: R for 'image quality'"""
        if self.image_paths:
            self.label_var.set("image quality")
            self.set_label_radio()
            self.jump_to_next_unclassified()

    def label_shortcut_t(self, event=None):
        """Keyboard shortcut: T for 'damaged'"""
        if self.image_paths:
            self.label_var.set("damaged")
            self.set_label_radio()
            self.jump_to_next_unclassified()

    def label_shortcut_y(self, event=None):
        """Keyboard shortcut: Y for 'other'"""
        if self.image_paths:
            self.label_var.set("other")
            self.set_label_radio()
            self.jump_to_next_unclassified()

    def prev_image_shortcut(self, event=None):
        """Keyboard shortcut: Left arrow for previous image"""
        self.prev_image()

    def next_image_shortcut(self, event=None):
        """Keyboard shortcut: Right arrow for next image"""
        self.next_image()

    def on_total_changed(self, event=None):
        """Called when the total parcels field changes"""
        self.update_total_stats()

    def on_filter_changed(self, value=None):
        """Called when the filter dropdown changes"""
        self.apply_filter()

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
        lines = ["Images:"]
        for label in LABELS:
            lines.append(f"  {label}: {counts[label]}")
        self.count_var.set("\n".join(lines))

    def update_progress_display(self):
        """Update the progress counter showing classified vs total images"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            self.progress_var.set("")
            return
        
        total_images = len(self.all_image_paths)
        classified_images = len([path for path in self.all_image_paths if path in self.labels and self.labels[path] != "(Unclassified)"])
        unclassified_images = total_images - classified_images
        
        # Multi-line format for better readability
        progress_text = f"Progress:\n{classified_images}/{total_images} classified\n({unclassified_images} remaining)"
        self.progress_var.set(progress_text)

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
        """Auto-detect total number of groups by counting unique ID+Timestamp combinations in filenames"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return
        
        unique_groups = set()
        for path in self.all_image_paths:
            group_id = self.get_parcel_number(path)
            if group_id:  # Only add non-empty group IDs
                unique_groups.add(group_id)
        
        if len(unique_groups) > 0:
            # Set the total parcels field with the count of unique ID+timestamp groups
            self.total_parcels_var.set(str(len(unique_groups)))
            # Update statistics immediately
            self.update_total_stats()

    def on_window_resize(self, event):
        """Handle window resize events to update image display"""
        # Only respond to resize events from the main window
        if event.widget == self.root and hasattr(self, 'image_paths') and self.image_paths:
            # Use after_idle to ensure the window has finished resizing
            self.root.after_idle(self.show_image)

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

    def zoom_in(self):
        """Increase zoom level"""
        # Allow zoom in both fit mode and 1:1 mode
        if self.scale_1to1:
            self.zoom_level = min(self.zoom_level * 1.25, 5.0)  # Max 500% zoom
        else:
            # Switch to 1:1 mode and set zoom level
            self.scale_1to1 = True
            self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
            self.zoom_level = 1.25  # Start with 125% zoom
        self.show_image()

    def zoom_out(self):
        """Decrease zoom level"""
        # Allow zoom out in both fit mode and 1:1 mode
        if self.scale_1to1:
            self.zoom_level = max(self.zoom_level / 1.25, 0.1)  # Min 10% zoom
        else:
            # Switch to 1:1 mode and set zoom level
            self.scale_1to1 = True
            self.btn_1to1.config(text="Fit to Window", bg="#A5D6A7")
            self.zoom_level = 0.8  # Start with 80% zoom
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

    def generate_read_failure_folder(self):
        """Generate a timestamped folder and copy all 'read failure' images into it"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            messagebox.showwarning("No Images", "Please select a folder with images first.")
            return
        
        # Find all 'read failure' images
        read_failure_images = [path for path in self.all_image_paths 
                         if path in self.labels and self.labels[path] == "read failure"]
        
        if not read_failure_images:
            messagebox.showinfo("No Images", "No 'read failure' images found to copy.")
            return
        
        # Disable button during processing
        self.btn_gen_no_read.config(state='disabled', text="Generating...")
        
        # Use the progress display for feedback
        self.auto_detect_progress_var.set(f"Preparing to copy {len(read_failure_images)} 'read failure' images...")
        
        # Start processing in a separate thread to avoid freezing the UI
        import threading
        processing_thread = threading.Thread(target=self.process_read_failure_copy, args=(read_failure_images,))
        processing_thread.daemon = True
        processing_thread.start()

    def process_read_failure_copy(self, read_failure_images):
        """Process copying read failure images in a separate thread"""
        import shutil
        from datetime import datetime
        
        try:
            # Check if folder_path exists
            if not hasattr(self, 'folder_path') or not self.folder_path:
                raise Exception("No folder selected")
                
            # Create timestamped folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"read_failure_{timestamp}"
            destination_folder = os.path.join(self.folder_path, folder_name)
            
            # Create the directory
            os.makedirs(destination_folder, exist_ok=True)
            
            total_images = len(read_failure_images)
            copied = 0
            
            for image_path in read_failure_images:
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
            self.root.after(0, self.complete_read_failure_copy, total_images, folder_name)
            
        except Exception as e:
            # Error handling
            self.root.after(0, self.copy_error, str(e))

    def update_copy_progress(self, current, total, filename):
        """Update the progress display for copying"""
        progress_text = f"Copying {current}/{total}\n{filename}"
        self.auto_detect_progress_var.set(progress_text)

    def complete_read_failure_copy(self, total_copied, folder_name):
        """Complete the copy operation"""
        # Re-enable button
        self.btn_gen_no_read.config(state='normal', text="Gen Read Failure\nFolder")
        
        # Show completion message
        self.auto_detect_progress_var.set(f"Completed!\nCopied {total_copied} images to:\n{folder_name}")
        
        # Show success dialog
        messagebox.showinfo("Copy Complete", 
                          f"Successfully copied {total_copied} 'read failure' images to folder:\n{folder_name}")

    def copy_error(self, error_message):
        """Handle copy operation errors"""
        # Re-enable button
        self.btn_gen_no_read.config(state='normal', text="Gen Read Failure\nFolder")
        
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
        
        # Update UI state
        self.auto_timer_enabled.set(True)
        self.auto_timer_button.config(text="Stop", bg="#f44336", activebackground="#d32f2f")
        self.auto_timer_entry.config(state='disabled')
        
        # Disable all controls while auto-timer is running
        self.disable_ui_controls()
        
        interval_ms = int(interval_minutes * 60 * 1000)  # Convert minutes to milliseconds
        self.auto_timer_job = self.root.after(interval_ms, self.run_auto_detection_timer)
        
        # Start countdown display with status based on checkbox state
        if self.auto_detect_enabled.get():
            self.auto_timer_status_var.set("Monitoring for new files (auto-detection enabled)")
        else:
            self.auto_timer_status_var.set("Monitoring for new files (auto-detection disabled)")
        self.start_countdown(interval_minutes)
        
    def stop_auto_timer(self):
        """Stop the auto-timer"""
        if self.auto_timer_job:
            self.root.after_cancel(self.auto_timer_job)
            self.auto_timer_job = None
        
        # Stop countdown
        self.stop_countdown()
        
        # Update UI state
        self.auto_timer_enabled.set(False)
        self.auto_timer_button.config(text="Start", bg="#4CAF50", activebackground="#45a049")
        self.auto_timer_entry.config(state='normal')
        
        # Re-enable all controls when auto-timer is stopped
        self.enable_ui_controls()
        
        self.auto_timer_status_var.set("Monitoring stopped")

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
                self.auto_timer_status_var.set(f"Found {len(new_unlabeled_files)} new files\n(Auto-detection disabled)")
                # Update the CSV to mark these as unclassified
                for file_path in new_unlabeled_files:
                    self.labels[file_path] = "(Unclassified)"
                self.save_csv()
                self.update_counts()
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
        
        # Disable checkbox
        self.auto_detect_checkbox.config(state='disabled')
        
        # Disable entry fields
        self.total_parcels_entry.config(state='disabled')
        # Note: auto_timer_entry is already disabled when timer is running

    def enable_ui_controls(self):
        """Re-enable all UI controls after auto-classification completes"""
        # Enable navigation buttons
        self.btn_prev.config(state='normal')
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
        
        # Enable checkbox
        self.auto_detect_checkbox.config(state='normal')
        
        # Enable entry fields
        self.total_parcels_entry.config(state='normal')

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

if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror("Missing Dependency", "Please install Pillow: pip install pillow")
        exit(1)
    root = tk.Tk()
    app = ImageLabelTool(root)
    root.mainloop()
