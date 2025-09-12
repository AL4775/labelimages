import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import re

LABELS = ["no label", "no read", "unreadable"]

class ImageLabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Label Tool")
        self.root.configure(bg="#f0f0f0")  # Light gray background
        self.image_paths = []
        self.current_index = 0
        self.labels = {}
        self.folder_path = None
        self.csv_filename = None
        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        frame.pack(padx=10, pady=10)

        self.btn_select = tk.Button(frame, text="Select Folder", command=self.select_folder,
                                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                  padx=20, pady=8, relief="flat")
        self.btn_select.grid(row=0, column=0, columnspan=3, pady=5)

        # Total parcels input
        total_frame = tk.Frame(frame, bg="#f0f0f0")
        total_frame.grid(row=1, column=0, columnspan=3, pady=5)
        tk.Label(total_frame, text="Total Parcels:", bg="#f0f0f0", font=("Arial", 10)).pack(side=tk.LEFT)
        self.total_parcels_var = tk.StringVar()
        self.total_parcels_entry = tk.Entry(total_frame, textvariable=self.total_parcels_var, width=10,
                                          font=("Arial", 10), bg="white", relief="solid", bd=1)
        self.total_parcels_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.total_parcels_entry.bind('<KeyRelease>', self.on_total_changed)

        # Filter dropdown
        filter_frame = tk.Frame(frame, bg="#f0f0f0")
        filter_frame.grid(row=2, column=0, columnspan=3, pady=5)
        tk.Label(filter_frame, text="Filter:", bg="#f0f0f0", font=("Arial", 10)).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All images")
        filter_options = ["All images", "no label only", "no read only", "unreadable only"]
        self.filter_menu = tk.OptionMenu(filter_frame, self.filter_var, *filter_options, command=self.on_filter_changed)
        self.filter_menu.config(bg="#e0e0e0", font=("Arial", 10), relief="solid", bd=1)
        self.filter_menu.pack(side=tk.LEFT, padx=(5, 0))

        self.canvas = tk.Label(frame, bg="#f0f0f0", relief="solid", bd=2)
        self.canvas.grid(row=3, column=0, columnspan=3)

        self.btn_prev = tk.Button(frame, text="<< Prev", command=self.prev_image,
                                bg="#2196F3", fg="white", font=("Arial", 11, "bold"),
                                padx=15, pady=5, relief="flat")
        self.btn_prev.grid(row=4, column=0, pady=5)
        self.btn_next = tk.Button(frame, text="Next >>", command=self.next_image,
                                bg="#2196F3", fg="white", font=("Arial", 11, "bold"),
                                padx=15, pady=5, relief="flat")
        self.btn_next.grid(row=4, column=2, pady=5)

        # Radio buttons for labels
        self.label_var = tk.StringVar(value=LABELS[0])
        label_frame = tk.Frame(frame, bg="#f0f0f0", relief="solid", bd=1, padx=10, pady=5)
        label_frame.grid(row=5, column=0, columnspan=3, pady=5)
        
        label_colors = {"no label": "#FFB74D", "no read": "#F06292", "unreadable": "#BA68C8"}
        for i, label in enumerate(LABELS):
            rb = tk.Radiobutton(label_frame, text=label, variable=self.label_var, 
                              value=label, command=self.set_label_radio,
                              bg=label_colors[label], font=("Arial", 10, "bold"),
                              selectcolor="white", padx=10, pady=5)
            rb.grid(row=0, column=i, padx=10)

        self.status_var = tk.StringVar()
        self.status = tk.Label(frame, textvariable=self.status_var, bg="#f0f0f0", 
                             font=("Arial", 11), fg="#333333")
        self.status.grid(row=6, column=0, columnspan=3)

        self.count_var = tk.StringVar()
        self.count_label = tk.Label(frame, textvariable=self.count_var, bg="#f0f0f0",
                                  font=("Arial", 10), fg="#666666")
        self.count_label.grid(row=7, column=0, columnspan=3)

        self.parcel_count_var = tk.StringVar()
        self.parcel_count_label = tk.Label(frame, textvariable=self.parcel_count_var, 
                                         font=("Arial", 10, "bold"), bg="#f0f0f0", fg="#4CAF50")
        self.parcel_count_label.grid(row=8, column=0, columnspan=3, pady=(5, 0))

        self.parcel_stats_var = tk.StringVar()
        self.parcel_stats_label = tk.Label(frame, textvariable=self.parcel_stats_var, 
                                         font=("Arial", 10, "bold"), fg="#1976D2", bg="#f0f0f0")
        self.parcel_stats_label.grid(row=9, column=0, columnspan=3, pady=(5, 0))

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder_path = folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = os.path.join(folder, f"revision_{timestamp}.csv")
        
        # Filter images that end with "_" followed by a number
        all_files = [f for f in os.listdir(folder)
                     if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
        
        self.all_image_paths = []
        for f in all_files:
            filename_without_ext = os.path.splitext(f)[0]
            # Check if filename ends with "_" followed by one or more digits
            if re.search(r'_\d+$', filename_without_ext):
                self.all_image_paths.append(os.path.join(folder, f))
        
        self.all_image_paths.sort()
        self.current_index = 0
        self.labels = {}  # Reset labels for new folder
        self.load_csv()  # Try to load existing CSV if any
        self.apply_filter()  # Apply current filter to show appropriate images

    def show_image(self):
        if not self.image_paths:
            self.canvas.config(image='')
            self.status_var.set("No images loaded.")
            return
        path = self.image_paths[self.current_index]
        img = Image.open(path)
        img.thumbnail((400, 400))
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(image=self.tk_img)
        label = self.labels.get(path, LABELS[0])
        self.label_var.set(label)
        self.status_var.set(f"{os.path.basename(path)} ({self.current_index+1}/{len(self.image_paths)})")

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.show_image()

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
        self.labels[path] = self.label_var.get()
        self.save_csv()
        self.update_counts()
        self.update_parcel_stats()
        self.update_total_stats()
        
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
                "no label only": "no label",
                "no read only": "no read", 
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
        self.update_parcel_stats()
        self.update_total_stats()

    def load_csv(self):
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
                        with open(existing_csv, newline='', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            next(reader, None)  # Skip header if present
                            for row in reader:
                                if len(row) >= 2:  # Support both old and new format
                                    self.labels[row[0]] = row[1]
            return
        with open(self.csv_filename, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header if present
            for row in reader:
                if len(row) >= 2:  # Support both old and new format
                    self.labels[row[0]] = row[1]

    def save_csv(self):
        if not self.csv_filename:
            return
        with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['image_path', 'image_label', 'parcel_number', 'parcel_label'])
            
            # Calculate current parcel labels
            parcel_labels_dict = self.calculate_parcel_labels()
            
            for path, label in self.labels.items():
                parcel_num = self.get_parcel_number(path)
                parcel_label = parcel_labels_dict.get(parcel_num, "no label") if parcel_num else "no label"
                writer.writerow([path, label, parcel_num or "", parcel_label])

    def update_counts(self):
        counts = {label: 0 for label in LABELS}
        for label in self.labels.values():
            if label in counts:
                counts[label] += 1
        self.count_var.set("Images: " + ", ".join(f"{label}: {counts[label]}" for label in LABELS))

    def get_parcel_number(self, image_path):
        """Extract the parcel number from the image filename"""
        filename = os.path.basename(image_path)
        filename_without_ext = os.path.splitext(filename)[0]
        match = re.search(r'_(\d+)$', filename_without_ext)
        return match.group(1) if match else None

    def calculate_parcel_labels(self):
        """Calculate parcel labels based on the labeling rules and return a dict"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            return {}

        # Parcel images by their number suffix (use all images, not filtered)
        parcels = {}
        for path in self.all_image_paths:
            parcel_num = self.get_parcel_number(path)
            if parcel_num:
                if parcel_num not in parcels:
                    parcels[parcel_num] = []
                parcels[parcel_num].append(path)

        # Calculate parcel labels based on rules
        parcel_labels_dict = {}
        
        for parcel_num, parcel_paths in parcels.items():
            parcel_image_labels = [self.labels.get(path, LABELS[0]) for path in parcel_paths]
            
            # Apply parcel labeling rules
            if "no read" in parcel_image_labels:
                # If at least one image is "no read", parcel is "no read"
                parcel_labels_dict[parcel_num] = "no read"
            elif all(label == "no label" for label in parcel_image_labels):
                # If all images are "no label", parcel is "no label"
                parcel_labels_dict[parcel_num] = "no label"
            else:
                # Mix of "no label" and "unreadable", parcel is "unreadable"
                parcel_labels_dict[parcel_num] = "unreadable"
                
        return parcel_labels_dict

    def update_parcel_stats(self):
        """Calculate parcel statistics based on the labeling rules"""
        if not hasattr(self, 'all_image_paths') or not self.all_image_paths:
            self.parcel_count_var.set("")
            return

        parcel_labels_dict = self.calculate_parcel_labels()
        
        # Count parcels by label
        parcel_labels = {"no label": 0, "no read": 0, "unreadable": 0}
        for parcel_label in parcel_labels_dict.values():
            if parcel_label in parcel_labels:
                parcel_labels[parcel_label] += 1

        total_parcels = len(parcel_labels_dict)
        stats_text = f"Parcels ({total_parcels}): " + ", ".join(f"{label}: {count}" for label, count in parcel_labels.items())
        self.parcel_count_var.set(stats_text)

    def update_total_stats(self):
        """Calculate statistics against manually entered total parcels"""
        try:
            total_entered = int(self.total_parcels_var.get()) if self.total_parcels_var.get() else 0
        except ValueError:
            self.parcel_stats_var.set("")
            return

        if total_entered <= 0:
            self.parcel_stats_var.set("")
            return

        # Get current parcel counts
        parcel_labels_dict = self.calculate_parcel_labels()
        parcel_counts = {"no label": 0, "no read": 0, "unreadable": 0}
        for parcel_label in parcel_labels_dict.values():
            if parcel_label in parcel_counts:
                parcel_counts[parcel_label] += 1

        # Calculate "read" as complement (total - no_read - unreadable)
        read_count = total_entered - parcel_counts["no read"] - parcel_counts["unreadable"]
        
        # Calculate percentages
        no_label_pct = (parcel_counts["no label"] / total_entered) * 100
        no_read_pct = (parcel_counts["no read"] / total_entered) * 100
        unreadable_pct = (parcel_counts["unreadable"] / total_entered) * 100
        read_pct = (read_count / total_entered) * 100 if read_count >= 0 else 0

        stats_text = (f"Total {total_entered}: no_label {parcel_counts['no label']} ({no_label_pct:.1f}%), "
                     f"no_read {parcel_counts['no read']} ({no_read_pct:.1f}%), "
                     f"unreadable {parcel_counts['unreadable']} ({unreadable_pct:.1f}%), "
                     f"read {read_count} ({read_pct:.1f}%)")
        
        self.parcel_stats_var.set(stats_text)

if __name__ == "__main__":
    try:
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror("Missing Dependency", "Please install Pillow: pip install pillow")
        exit(1)
    root = tk.Tk()
    app = ImageLabelTool(root)
    root.mainloop()
