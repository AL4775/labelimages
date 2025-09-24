"""
🎨 Chart Demonstration Script for Image Label Tool

This script demonstrates the new fancy chart features including:
- 📊 Histogram for image classification distribution
- 🥧 Pie chart for parcel breakdown 
- 📈 Progress overview with multiple visualizations

Features:
✨ Beautiful color schemes with modern styling
✨ Interactive charts with hover effects
✨ Multiple chart types in tabbed interface
✨ Professional statistical breakdowns
✨ Real-time data visualization
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import tkinter as tk
from tkinter import ttk

def demo_charts():
    """Demonstration of the chart functionality"""
    
    # Sample data for demonstration
    sample_image_data = {
        "(Unclassified)": 15,
        "no code": 25,
        "read failure": 8,
        "occluded": 12,
        "image quality": 6,
        "damaged": 4,
        "other": 3
    }
    
    sample_parcel_data = {
        "no code": 18,
        "read failure": 5,
        "occluded": 8,
        "image quality": 4,
        "damaged": 2,
        "other": 2
    }
    
    # Create demo window
    root = tk.Tk()
    root.title("📊 Chart Demo - Image Label Tool")
    root.geometry("1200x800")
    root.configure(bg="#FAFAFA")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Demo Tab 1: Histogram
    hist_frame = ttk.Frame(notebook)
    notebook.add(hist_frame, text="📊 Image Histogram")
    
    # Create histogram
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    labels = list(sample_image_data.keys())
    counts = list(sample_image_data.values())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
    
    bars = ax1.bar(range(len(labels)), counts, color=colors[:len(labels)], 
                   alpha=0.8, edgecolor='white', linewidth=2)
    
    ax1.set_title('📊 Image Classification Distribution', fontsize=16, fontweight='bold', pad=20)
    ax1.set_xlabel('Classification Labels', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Images', fontsize=12, fontweight='bold')
    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
    
    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, counts)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
               str(count), ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_axisbelow(True)
    plt.tight_layout()
    
    canvas1 = FigureCanvasTkAgg(fig1, master=hist_frame)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Demo Tab 2: Pie Chart
    pie_frame = ttk.Frame(notebook)
    notebook.add(pie_frame, text="🥧 Parcel Pie Chart")
    
    fig2, (ax2, ax3) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Pie chart
    pie_labels = list(sample_parcel_data.keys())
    pie_sizes = list(sample_parcel_data.values())
    
    wedges, texts, autotexts = ax2.pie(pie_sizes, labels=pie_labels, colors=colors[:len(pie_labels)],
                                      autopct='%1.1f%%', startangle=90, 
                                      explode=[0.05] * len(pie_labels),
                                      shadow=True, textprops={'fontsize': 10})
    
    ax2.set_title('🥧 Parcel Classification Breakdown', fontsize=14, fontweight='bold', pad=20)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    # Table
    ax3.axis('tight')
    ax3.axis('off')
    
    total_parcels = sum(pie_sizes)
    table_data = []
    for label, count in zip(pie_labels, pie_sizes):
        percentage = (count / total_parcels) * 100 if total_parcels > 0 else 0
        table_data.append([label, str(count), f"{percentage:.1f}%"])
    
    table_data.append(['TOTAL', str(total_parcels), '100.0%'])
    
    table = ax3.table(cellText=table_data,
                     colLabels=['Classification', 'Count', 'Percentage'],
                     cellLoc='center', loc='center',
                     colColours=['#E3F2FD', '#E3F2FD', '#E3F2FD'])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    ax3.set_title('📊 Detailed Breakdown', fontsize=12, fontweight='bold')
    plt.tight_layout()
    
    canvas2 = FigureCanvasTkAgg(fig2, master=pie_frame)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Add info label
    info_label = tk.Label(root, 
                         text="🎨 These are the new fancy charts available in Image Label Tool!\n" +
                              "Click 'Show Charts' button in the toolbar to see real data visualizations.",
                         bg="#FAFAFA", font=("Arial", 10), fg="#666666")
    info_label.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print("🎨 Starting Chart Demonstration...")
    demo_charts()