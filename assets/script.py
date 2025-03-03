import matplotlib.pyplot as plt
import numpy as np

# Set up the figure with dark background
plt.figure(figsize=(10, 4), facecolor='#1a202c')
ax = plt.subplot()
ax.set_facecolor('#1a202c')

# Data from your benchmark - memory usage in MB
tools = ['Pathik', 'Playwright']
memory = [0.17, 17.44]  # Memory usage from batch size 5
ratio = memory[1] / memory[0]  # About 103x less memory

# Create horizontal bars
y_pos = np.arange(len(tools))
bars = ax.barh(y_pos, memory, height=0.6, color=['#4fc3f7', '#9e9e9e'])

# Add labels and styling
ax.set_yticks(y_pos)
ax.set_yticklabels(tools, fontsize=12, color='white')
ax.invert_yaxis()  # Invert to match your example image

# Add memory values at the end of each bar
for i, bar in enumerate(bars):
    width = bar.get_width()
    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
            f'{width:.2f}MB', ha='left', va='center', color='white', fontsize=12)

# Set title showing memory efficiency
plt.title(f'Memory usage - {ratio:.0f}x less', fontsize=20, color='white', pad=20)

# Remove axes
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

# Remove tick marks
ax.tick_params(axis='both', which='both', length=0)
ax.set_xticks([])

# Add vertical grid lines to match example image
ax.grid(axis='x', linestyle='--', alpha=0.3, color='white')

# Add icons (if needed, you would need to import images for this)
# This is just a placeholder for where you'd add icon logic

plt.tight_layout()
plt.savefig('benchmarks/concurrency/batch_results.png', dpi=300, bbox_inches='tight')
plt.show()