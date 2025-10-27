from typing import List
import tkinter as tk
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFont

from utils import *

IMAGE_SIZE = 1200
DRAWING_SIZE = IMAGE_SIZE * 0.9
MAX_VERTEX_COUNT = 50
MAX_MODULUS = 1000
MAX_MULTIPLIER = MAX_MODULUS - 1

class ModularMultiplicationDisplay:    
    def __init__(self, image_size: int, drawing_width: int):
        self.vertex_count = 3
        self.modulus = 9
        self.multiplier = 2
        self.angle = 0 # in radians
        self.img_size = image_size
        self.drawing_width = drawing_width
        self.center = self.img_size // 2
        self.font = ImageFont.truetype(r"FreeMono.ttf", 20)

    def is_circle(self) -> bool:
        return self.vertex_count >= MAX_VERTEX_COUNT

    def compute_vertices(self) -> List[complex]:
        if self.is_circle():
            # no vertices in this case
            self.vertex_points = []
            return

        roots = np.exp(2j * np.pi * np.arange(self.vertex_count) / self.vertex_count)
        roots = rotate_points(roots, self.angle) * (self.drawing_width / 2)
        vertex_points = roots + complex(self.center, self.center)
        self.vertex_points = vertex_points

    def polygon_points(self, vertices, points_per_side):
        """Generate points along the edges of a polygon defined by the given vertices."""
        points = []
        for p1, p2 in zip(vertices, np.roll(vertices, -1)):
            for t in np.linspace(0, 1, points_per_side, endpoint=False):
                p = (1 - t) * p1 + t * p2
                points.append((p.real, p.imag))
        return points

    def compute_edge_points(self) -> List[complex]:
        if self.is_circle():
            angles = 2 * np.pi * np.arange(self.modulus) / self.modulus
            points = np.exp(1j * angles) * (self.drawing_width / 2)
            points = rotate_points(points, self.angle)
            points += complex(self.center, self.center)
            self.edge_points = list(map(lambda x: (x.real, x.imag), points))
            return

        points_per_side = self.modulus // self.vertex_count
        self.edge_points = self.polygon_points(self.vertex_points, points_per_side)

    def compute_connections(self):
        connections = []
        for i, _ in enumerate(self.edge_points):
            end_index = (i * self.multiplier) % (len(self.edge_points))
            connections.append((i, end_index))
        self.connections = connections

    def change_parameters(self, vertex_count: int, modulus: int, multiplier: int, angle: float):
        vertex_count_changed = self.vertex_count != vertex_count
        modulus_changed = self.modulus != modulus
        multiplier_changed = self.multiplier != multiplier
        angle_changed = self.angle != angle
        actual_modulus_prev = len(self.edge_points) if hasattr(self, 'edge_points') else 0

        self.angle = angle
        if angle_changed or vertex_count_changed:
            self.vertex_count = vertex_count
            self.compute_vertices()

        if angle_changed or vertex_count_changed or modulus_changed:
            self.modulus = modulus
            self.compute_edge_points()

        actual_modulus_changed = actual_modulus_prev != len(self.edge_points)
        if actual_modulus_changed or multiplier_changed:
            self.multiplier = multiplier
            self.compute_connections()

    def draw_vertex_connections(self):
        if self.is_circle():
            self.draw.ellipse([
                (self.center - self.drawing_width / 2, self.center - self.drawing_width / 2),
                (self.center + self.drawing_width / 2, self.center + self.drawing_width / 2)
            ], outline="white")
        else:
            self.draw.polygon([(p.real, p.imag) for p in self.vertex_points], outline="white")

    def draw_multiplication_connections(self):
        for start_idx, end_idx in self.connections:
            start_point = self.edge_points[start_idx]
            end_point = self.edge_points[end_idx]
            self.draw.line([start_point, end_point], fill="white")

    def get_image(self):
        self.img = Image.new("RGB", (self.img_size, self.img_size), "black")
        self.draw = ImageDraw.Draw(self.img)
        self.draw_vertex_connections()
        self.draw_multiplication_connections()
        is_circle = self.vertex_count >= MAX_VERTEX_COUNT
        self.draw.text((40,5), f"Modular multiplication {'polygon' if not is_circle else 'circle'}{f', V={self.vertex_count}' if not is_circle else ''}, M={self.modulus}, K={self.multiplier}", font=self.font, align = "left", fill = "white")
        return self.img


class GUI:
    def __init__(self, root):
        self.display = ModularMultiplicationDisplay(IMAGE_SIZE, DRAWING_SIZE)

        canvas_frame = tk.Frame(root)
        canvas_frame.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, width=IMAGE_SIZE, height=IMAGE_SIZE, bg="white")
        self.canvas.pack(fill="both", expand=True)

        controls_frame = tk.Frame(root)
        controls_frame.pack(side="bottom", fill="x", pady=5)

        self.sliders = {}

        def make_slider_row(parent, label_text, from_, to_, default, callback=None):
            frame = tk.Frame(parent)
            frame.pack(fill="x", pady=2)

            tk.Label(frame, text=label_text, width=12, anchor="w").pack(side="left")

            var = tk.IntVar(value=default)

            slider = tk.Scale(
                frame, from_=from_, to=to_, orient="horizontal",
                variable=var, showvalue=False, command=lambda _: callback() if callback else None
            )
            slider.pack(side="left", fill="x", expand=True, padx=5)

            entry = tk.Entry(frame, width=5, textvariable=var)
            entry.pack(side="left", padx=5)

            entry.bind("<Return>", lambda e: callback() if callback else None)

            return var, slider

        self.vertex_var, self.sliders['vertex'] = make_slider_row(
            controls_frame, "Vertex count:", 3, MAX_VERTEX_COUNT, 3, self.update_display
        )
        self.modulus_var, self.sliders['modulus'] = make_slider_row(
            controls_frame, "Modulus:", 1, MAX_MODULUS, 100, self.update_display
        )
        self.multiplier_var, self.sliders['multiplier'] = make_slider_row(
            controls_frame, "Multiplier:", 0, MAX_MODULUS, 2, self.update_display
        )
        self.angle_var, self.sliders['angle'] = make_slider_row(
            controls_frame, "Angle:", -180, 180, -150, self.update_display
        )

        def update_multiplier_max(*args):
            new_max = self.modulus_var.get()
            self.sliders['multiplier'].config(to=new_max)
            if self.multiplier_var.get() > new_max:
                self.multiplier_var.set(new_max)

        self.modulus_var.trace_add("write", update_multiplier_max)
        update_multiplier_max()

        self.tk_img = None
        self.update_display()

    def update_display(self, *args):
        vertex_count = self.vertex_var.get()
        modulus = self.modulus_var.get()
        multiplier = self.multiplier_var.get()
        angle = np.radians(self.angle_var.get())

        self.display.change_parameters(vertex_count, modulus, multiplier, angle)
        img = self.display.get_image()

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Modular Multiplication Visualization")
    root.geometry(f"{int(IMAGE_SIZE)}x{int(IMAGE_SIZE+130)}")
    app = GUI(root)
    root.mainloop()
