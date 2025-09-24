#!/usr/bin/env python3
"""
Quick demo of the fancy chart functionality
"""
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import os

class ChartDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chart Demo - Image Label Tool v6.0.0")
        self.root.geometry("800x600")
        
        # Create test data
        self.image_data = {'cat': 45, 'dog': 32, 'bird': 23, 'fish': 18}
        self.parcel_data = {'small': 30, 'medium': 40, 'large': 20, 'xlarge': 10}
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="🎨 Fancy Charts Demo", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        # Chart buttons
        tk.Button(btn_frame, text="📊 Show Histogram", 
                 command=self.show_histogram, bg='lightblue').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🥧 Show Pie Chart", 
                 command=self.show_pie_chart, bg='lightgreen').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📈 Show Progress", 
                 command=self.show_progress, bg='lightyellow').pack(side=tk.LEFT, padx=5)
        
        # Chart area
        self.chart_frame = tk.Frame(self.root, bg='white', relief='sunken', bd=2)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def show_histogram(self):
        self.clear_chart_frame()
        
        # Create histogram
        fig, ax = plt.subplots(figsize=(10, 6))
        categories = list(self.image_data.keys())
        counts = list(self.image_data.values())
        
        bars = ax.bar(categories, counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax.set_title('Image Distribution Histogram', fontsize=16, fontweight='bold')
        ax.set_xlabel('Image Categories', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def show_pie_chart(self):
        self.clear_chart_frame()
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 6))
        labels = list(self.parcel_data.keys())
        sizes = list(self.parcel_data.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                         startangle=90, explode=(0.05, 0, 0, 0))
        ax.set_title('Parcel Size Distribution', fontsize=16, fontweight='bold')
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_color('white')
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def show_progress(self):
        self.clear_chart_frame()
        
        # Create progress overview with multiple subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        
        # Subplot 1: Bar chart
        categories = list(self.image_data.keys())
        counts = list(self.image_data.values())
        ax1.bar(categories, counts, color='lightblue')
        ax1.set_title('Images by Category')
        ax1.set_ylabel('Count')
        
        # Subplot 2: Line chart (progress over time)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        progress = [10, 25, 40, 65, 85]
        ax2.plot(days, progress, marker='o', linewidth=2, color='green')
        ax2.set_title('Labeling Progress')
        ax2.set_ylabel('Percentage')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # Subplot 3: Donut chart
        sizes = list(self.parcel_data.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        ax3.pie(sizes, colors=colors, wedgeprops=dict(width=0.5))
        ax3.set_title('Parcel Distribution')
        
        # Subplot 4: Text summary
        ax4.axis('off')
        summary = f"""
📊 Summary Statistics:
        
Total Images: {sum(self.image_data.values())}
Categories: {len(self.image_data)}
        
Completion Rate: 78%
Quality Score: 95%
        
🎯 Ready for Export!
        """
        ax4.text(0.1, 0.5, summary, fontsize=12, verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.suptitle('Progress Overview Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def clear_chart_frame(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        demo = ChartDemo()
        demo.run()
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install matplotlib seaborn")
    except Exception as e:
        print(f"❌ Error: {e}")