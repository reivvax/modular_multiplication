from typing import List
import numpy as np

def clean_complex(values: List[complex], tol: float = 1e-10) -> List[complex]:
    for i, c in enumerate(values):
        if not isinstance(c, complex):
            raise ValueError("Input must be a list of complex numbers.")
        if abs(c.real) < tol:
            values[i] = complex(0, c.imag)
        if abs(c.imag) < tol:
            values[i] = complex(c.real, 0)

    return values


def rotate_points(points, angle):
    return points * np.exp(1j * angle)
