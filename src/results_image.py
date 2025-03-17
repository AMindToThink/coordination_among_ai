import matplotlib.pyplot as plt
import numpy as np

# Data
categories = ['4o-Mini\nCollaboration', '4o-Mini', '3 Saboteurs', 
              'Expected\nSaboteurs', 'Worst-Case\nCollaborators\nvs Saboteurs']
values = [92, 90, 20.27, 8, 86]

# Create figure and axis
fig, ax = plt.subplots(figsize=(12, 8))

# Set background color to white
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Create bars
bar_width = 0.6
bar_positions = np.arange(len(categories))
bars = ax.bar(bar_positions, values, width=bar_width, color='#4285F4', edgecolor='black', linewidth=1)

# Add baseline
ax.axhline(y=25, color='orange', linestyle='--', linewidth=2, label='Random Baseline (25%)')

# Add values on top of bars
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{values[i]}%', ha='center', va='bottom', fontsize=12)

# Customize x-axis
ax.set_xticks(bar_positions)
ax.set_xticklabels(categories, rotation=0, ha='center', fontsize=12)

# Customize y-axis
ax.set_ylim(0, 100)
ax.set_yticks(range(0, 101, 20))
ax.set_yticklabels([f'{y}%' for y in range(0, 101, 20)], fontsize=12)
ax.set_ylabel('Percentage (%)', fontsize=14)

# Add grid lines for better readability
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Add title
plt.title('Performance Comparison', fontsize=16, pad=20)

# Add legend for the baseline
plt.legend(loc='upper right')

# Adjust layout
plt.tight_layout()

# Show plot
plt.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
plt.show()