"""
Demo visualization script to help users understand score heatmaps.
This creates simple example heatmaps that show the concept clearly.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from io import BytesIO
import base64

def create_demo_heatmap():
    """Create a simple demo heatmap to show users how to interpret scores."""
    # Create a simple 10x10 grid with example data
    demo_grid = np.zeros((10, 10))
    
    # Add some high-activity areas (red zones)
    demo_grid[2:4, 7:9] = 9  # High feeding area
    demo_grid[6:8, 2:4] = 8  # High bedding area
    demo_grid[4, 4:7] = 9    # Travel corridor
    
    # Add some medium areas (yellow zones)
    demo_grid[1:3, 1:3] = 6  # Medium area
    demo_grid[7:9, 7:9] = 7  # Medium area
    
    # Add some low areas (blue zones) - already 0
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create the heatmap
    im = ax.imshow(demo_grid, cmap='RdYlBu_r', vmin=0, vmax=10)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Deer Activity Score', fontsize=12)
    cbar.set_ticks([0, 2, 4, 6, 8, 10])
    cbar.set_ticklabels(['Very Low', 'Low', 'Moderate', 'Good', 'High', 'Excellent'])
    
    # Add title and labels
    ax.set_title('Example: How to Read Deer Activity Heatmaps', fontsize=14, fontweight='bold')
    ax.set_xlabel('Grid East-West')
    ax.set_ylabel('Grid North-South')
    
    # Add annotations
    ax.annotate('🔴 HUNT HERE!\n(Score 8-9)', xy=(8, 3), xytext=(8, 1),
                arrowprops=dict(arrowstyle='->', color='black', lw=2),
                fontsize=10, ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.annotate('🔴 HUNT HERE!\n(Score 9)', xy=(6, 4), xytext=(8, 6),
                arrowprops=dict(arrowstyle='->', color='black', lw=2),
                fontsize=10, ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.annotate('🟡 Good Option\n(Score 6-7)', xy=(2, 8), xytext=(4, 9),
                arrowprops=dict(arrowstyle='->', color='black', lw=2),
                fontsize=10, ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.annotate('🔵 Avoid\n(Score 0)', xy=(1, 1), xytext=(3, 2),
                arrowprops=dict(arrowstyle='->', color='black', lw=2),
                fontsize=10, ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Convert to base64 for web display
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"

if __name__ == "__main__":
    # Generate demo and save
    demo_image = create_demo_heatmap()
    print("Demo heatmap created successfully!")
    print("Use this in your Streamlit app to help users understand the concept.")
