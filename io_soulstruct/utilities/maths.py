from __future__ import annotations

__all__ = [
    "np_cross",
]

import numpy as np

def np_cross(array_a: np.ndarray, array_b: np.ndarray) -> np.ndarray:
    """Hack for PyCharm/Numpy conflict where `np.cross` is typed as `NoReturn` for boolean arrays. Both sides seem
    to be pointing fingers at the other for this. Personally, I think it's stupid for Numpy to force type checkers
    to handle function overloads so precisely. The `np.cross` docs don't even say anything about the bool case!

    See line 506 in `numpy/core/numeric.pyi`.
    """
    return np.cross(array_a, array_b)
