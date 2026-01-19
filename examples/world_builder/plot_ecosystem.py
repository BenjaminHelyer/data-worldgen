"""
Visualization script for ecosystem data.

Creates a matplotlib plot showing:
- Top: Distribution of species (bar chart)
- Bottom: Conditional distributions of age given species (2x3 grid of individual plots)
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# Set up paths
current_dir = Path(__file__).resolve().parent
parquet_file = current_dir / "ecosystem.parquet"

# Load the data
if not parquet_file.exists():
    raise FileNotFoundError(
        f"Parquet file not found: {parquet_file}\n"
        "Please run ecosystem_example.py first to generate the data."
    )

df = pd.read_parquet(parquet_file)

# Create figure with custom layout using GridSpec
# Top row takes more space, bottom has 2 rows x 3 cols
fig = plt.figure(figsize=(14, 12))
gs = GridSpec(3, 3, figure=fig, height_ratios=[2, 1, 1], hspace=0.5, wspace=0.3)
fig.suptitle("Ecosystem Species and Age Distributions", fontsize=16, fontweight="bold")

# Top plot: Species distribution (spans all 3 columns)
ax1 = fig.add_subplot(gs[0, :])
species_counts = df["species"].value_counts().sort_index()
species_names = species_counts.index.tolist()
counts = species_counts.values.tolist()

# Use a nice color palette
colors_top = plt.cm.viridis(np.linspace(0.2, 0.8, len(species_names)))
bars = ax1.bar(species_names, counts, color=colors_top, edgecolor="black", alpha=0.8, linewidth=1.2)
ax1.set_xlabel("Species", fontsize=12, fontweight="bold")
ax1.set_ylabel("Count", fontsize=12, fontweight="bold")
ax1.set_title("Distribution of Species", fontsize=14, fontweight="bold")
ax1.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.8)

# Add count labels on top of bars
for bar in bars:
    height = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        height,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
    )

# Rotate x-axis labels if needed
ax1.tick_params(axis="x", rotation=45)
# Move x-axis label down to avoid overlap with bottom plots
ax1.xaxis.set_label_coords(0.5, -0.15)

# Bottom plots: Conditional age distributions by species (2x3 grid)
species_list = sorted(df["species"].unique())
colors_bottom = plt.cm.tab10(np.linspace(0, 1, len(species_list)))

# Create individual histogram for each species in a 2x3 grid
for i, species in enumerate(species_list):
    row = 1 + (i // 3)  # Row 1 or 2 (0-indexed from top, but we start at row 1)
    col = i % 3  # Column 0, 1, or 2
    
    ax = fig.add_subplot(gs[row, col])
    species_data = df[df["species"] == species]["age"]
    
    if len(species_data) > 0:
        ax.hist(
            species_data,
            bins=20,
            alpha=0.7,
            color=colors_bottom[i],
            edgecolor="black",
            linewidth=0.8,
            density=True,
        )
        ax.set_title(f"{species}\n(n={len(species_data)})", fontsize=10, fontweight="bold")
        ax.set_xlabel("Age (years)", fontsize=9, fontweight="bold")
        ax.set_ylabel("Probability Density", fontsize=9, fontweight="bold")
        ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
        ax.set_xlim(left=0)  # Start x-axis at 0 for age
        ax.tick_params(labelsize=8)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the plot
output_file = current_dir / "ecosystem_plot.png"
plt.savefig(output_file, dpi=300, bbox_inches="tight")
print(f"Plot saved to: {output_file}")

# Close the figure to free memory
plt.close()
