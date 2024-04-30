import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# Create a graph for a simplified version of the IEEE 13 bus system
G = nx.Graph()

# Adding nodes (buses) and edges (lines) to the graph
# Note: The IEEE 13 bus system is more complex; this is a simplified representation
G.add_edges_from([
    (1, 2), (2, 3), (3, 4), (4, 5), (3, 6), (6, 7), (7, 8), 
    (3, 9), (9, 10), (10, 11), (11, 12), (12, 13)
])

# Assigning positions to each node for visual representation
pos = {
    1: (0, 4), 2: (1, 4), 3: (2, 4), 4: (3, 4), 5: (4, 4),
    6: (2, 3), 7: (3, 3), 8: (4, 3),
    9: (2, 2), 10: (3, 2), 11: (4, 2), 12: (5, 2), 13: (6, 2)
}

# Create a parabolic PV generation profile to overlay at node 5
x = np.linspace(3, 5, 100)
y = -1 * (x - 4)**2 + 5.5  # Parabola peaking at 5.5 (above node 5)

# Drawing the network
plt.figure(figsize=(12, 8))
nx.draw(G, pos, with_labels=True, node_size=1000, node_color="skyblue")

# Drawing the PV generation curve
plt.plot(x, y, color="orange", label="PV Generation Curve")

# Annotating the node with PV generation
plt.annotate('PV Generation', xy=(4, 4), xytext=(5, 5),
             arrowprops=dict(facecolor='orange', shrink=0.05), fontsize=12)

# Displaying the legend
plt.legend()

# Set the title and show the plot
plt.title("Simplified IEEE 13 Bus System with PV Generation")
plt.grid(True)
plt.show()
