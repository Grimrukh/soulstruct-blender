from __future__ import annotations

__all__ = [
    "HKX_MATERIAL_NAME_RE",
]

import re


HKX_MATERIAL_NAME_RE = re.compile(r"HKX (?P<index>\d+) \((?P<res>Hi|Lo)\).*")  # Blender HKX material name
