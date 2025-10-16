import tkinter as tk
from tkinter import simpledialog, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import numpy as np
import time

class NetworkSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Topology Simulator")
        self.network = nx.Graph()
        self.node_types = {}  # node: type mapping

        # GUI Buttons
        tk.Button(root, text="Add Node", command=self.add_node, width=25, bg="#6C63FF", fg="white").pack(pady=5)
        tk.Button(root, text="Add Connection", command=self.add_connection, width=25, bg="#2196F3", fg="white").pack(pady=5)
        tk.Button(root, text="Show Topology", command=self.show_topology, width=25, bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(root, text="Send Packet (Animated)", command=self.animate_packet, width=25, bg="#FF9800", fg="white").pack(pady=5)
        tk.Button(root, text="Exit", command=root.quit, width=25, bg="#F44336", fg="white").pack(pady=5)

        # Node emoji and color mapping
        self.node_icons = {"pc": "🖥️", "router": "🌐", "switch": "🔀"}
        self.node_colors = {"pc": "#4CAF50", "router": "#2196F3", "switch": "#9C27B0"}

    def add_node(self):
        node = simpledialog.askstring("Add Node", "Enter node name:")
        if not node:
            return
        node_type = simpledialog.askstring("Node Type", "Enter node type (PC / Router / Switch):")
        if node_type and node_type.lower() in ["pc", "router", "switch"]:
            self.network.add_node(node)
            self.node_types[node] = node_type.lower()
            messagebox.showinfo("Success", f"{node_type.capitalize()} '{node}' added successfully!")
        else:
            messagebox.showerror("Error", "Invalid type! Enter PC, Router, or Switch.")

    def add_connection(self):
        n1 = simpledialog.askstring("Add Connection", "Enter first node:")
        n2 = simpledialog.askstring("Add Connection", "Enter second node:")
        if n1 in self.network.nodes and n2 in self.network.nodes:
            self.network.add_edge(n1, n2)
            messagebox.showinfo("Success", f"Connected '{n1}' ↔ '{n2}'")
        else:
            messagebox.showerror("Error", "Both nodes must exist before connecting!")

    def show_topology(self):
        if len(self.network.nodes) == 0:
            messagebox.showwarning("Empty", "No nodes to display!")
            return

        plt.figure(figsize=(7, 5))
        pos = nx.spring_layout(self.network, seed=42)
        ax = plt.gca()
        ax.clear()

        # Draw edges
        nx.draw_networkx_edges(self.network, pos, ax=ax)

        # Draw emoji nodes
        for node, ntype in self.node_types.items():
            x, y = pos[node]
            ax.text(x, y, self.node_icons[ntype], fontsize=20, ha='center', va='center', color=self.node_colors[ntype])
            ax.annotate(f"{node}\nType: {ntype.capitalize()}", xy=(x, y),
                        textcoords="offset points", xytext=(0, 15),
                        ha="center", fontsize=8, color="black")

        nx.draw_networkx_labels(self.network, pos, ax=ax, font_size=12)
        plt.title("Network Topology (Emoji Nodes)")
        plt.axis('off')
        plt.show()

    def animate_packet(self):
        if len(self.network.nodes) < 2:
            messagebox.showerror("Error", "Need at least 2 nodes to simulate packet transfer!")
            return

        src = simpledialog.askstring("Send Packet", "Enter Source Node:")
        dst = simpledialog.askstring("Send Packet", "Enter Destination Node:")
        if src not in self.network.nodes or dst not in self.network.nodes:
            messagebox.showerror("Error", "Both nodes must exist!")
            return

        try:
            path = nx.shortest_path(self.network, source=src, target=dst)
            messagebox.showinfo("Packet Info", f"Packet path: {path}")
            self._animate_path(path, src, dst)
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", f"No path exists between {src} and {dst}!")

    def _animate_path(self, path, src, dst):
        pos = nx.spring_layout(self.network, seed=42)

        # Tkinter window for Matplotlib canvas
        anim_window = tk.Toplevel(self.root)
        anim_window.title("Packet Animation")
        fig, ax = plt.subplots(figsize=(7, 5))
        canvas = FigureCanvasTkAgg(fig, master=anim_window)
        canvas.get_tk_widget().pack()

        ax.clear()
        nx.draw_networkx_edges(self.network, pos, ax=ax)
        for node, ntype in self.node_types.items():
            x, y = pos[node]
            ax.text(x, y, self.node_icons[ntype], fontsize=20, ha='center', va='center', color=self.node_colors[ntype])
            ax.annotate(f"{node}\nType: {ntype.capitalize()}", xy=(x, y),
                        textcoords="offset points", xytext=(0, 15),
                        ha="center", fontsize=8, color="black")
        nx.draw_networkx_labels(self.network, pos, ax=ax, font_size=12)
        ax.set_title("Packet Flow Animation")
        ax.axis('off')

        packet_dot, = ax.plot([], [], 'ro', markersize=12)

        # Smooth path points
        segment_points = []
        for i in range(len(path) - 1):
            start = np.array(pos[path[i]])
            end = np.array(pos[path[i + 1]])
            for t in np.linspace(0, 1, 25):
                segment_points.append(start * (1 - t) + end * t)

        # Packet monitor popup
        monitor = tk.Toplevel(self.root)
        monitor.title("Packet Monitor")
        monitor.geometry("300x150")
        monitor_label = tk.Label(monitor, text="", font=("Arial", 12))
        monitor_label.pack(pady=20)

        total_hops = len(path) - 1
        start_time = time.time()

        def init():
            packet_dot.set_data([], [])
            return packet_dot,

        def update(frame):
            x, y = segment_points[frame]
            packet_dot.set_data(x, y)
            canvas.draw()  # update canvas to show movement

            hop_index = min(frame // 25, total_hops - 1)
            current_hop = f"{path[hop_index]} → {path[hop_index+1]}"
            progress = int((frame+1)/len(segment_points)*100)
            elapsed = time.time() - start_time
            monitor_label.config(text=f"Current Hop: {current_hop}\nTotal Hops: {total_hops}\nProgress: {progress}%\nTime: {elapsed:.1f}s\nStatus: In Transit")
            return packet_dot,

        def on_animation_end():
            monitor_label.config(text=f"Packet delivered from {src} to {dst}!\nTotal Time: {time.time()-start_time:.1f}s")
            monitor.after(2000, monitor.destroy)
            messagebox.showinfo("Delivery Status", f"Packet successfully delivered from {src} to {dst}!")

        ani = animation.FuncAnimation(fig, update, frames=len(segment_points),
                                      init_func=init, interval=100, blit=True, repeat=False)
        fig.canvas.mpl_connect('close_event', lambda event: on_animation_end())

# Run GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulator(root)
    root.geometry("350x400")
    root.mainloop()

