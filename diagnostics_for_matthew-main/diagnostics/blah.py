import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl

def plot_attention_mapping():
    # Set font family that supports Japanese
    plt.rcParams['font.family'] = 'MS Gothic'  # or try 'Noto Sans JP' if installed
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define the words
    eng_words = ['I', 'love', 'running']
    jpn_words = ['ジョギング', '好きです', '∅']
    
    # Position words
    eng_x = np.arange(len(eng_words))
    jpn_x = np.arange(len(jpn_words))
    eng_y = np.ones_like(eng_x)
    jpn_y = np.zeros_like(jpn_x)
    
    # Plot words
    ax.scatter(eng_x, eng_y, alpha=0)
    ax.scatter(jpn_x, jpn_y, alpha=0)
    
    # Add word labels
    for i, word in enumerate(eng_words):
        ax.annotate(word, (eng_x[i], eng_y[i]), 
                   xytext=(0, 10), textcoords='offset points', 
                   ha='center', va='bottom', fontsize=12)
    
    for i, word in enumerate(jpn_words):
        ax.annotate(word, (jpn_x[i], jpn_y[i]), 
                   xytext=(0, -10), textcoords='offset points', 
                   ha='center', va='top', fontsize=12)
    
    # Draw attention lines with arrows
    connections = [
        (2, 0),  # running → ジョギング
        (1, 1),  # love → 好きです
        (0, 2),  # I → ∅
    ]
    
    for eng_idx, jpn_idx in connections:
        ax.annotate('', 
                   xy=(jpn_x[jpn_idx], jpn_y[0]),
                   xytext=(eng_x[eng_idx], eng_y[0]),
                   arrowprops=dict(arrowstyle='->',
                                 color='blue',
                                 alpha=0.5,
                                 linewidth=2))
    
    # Configure plot
    ax.set_ylim(-0.5, 1.5)
    ax.axis('off')
    plt.title('English → Japanese Translation Attention Mapping', pad=20)
    
    plt.tight_layout()
    plt.show()

# Generate the plot
plot_attention_mapping()