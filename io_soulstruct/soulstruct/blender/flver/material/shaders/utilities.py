from __future__ import annotations

__all__ = [
    "TEX_SAMPLER_RE",
]

import re

TEX_SAMPLER_RE = re.compile(r"(Main) (\d+) (Albedo|Specular|Shininess|Normal)")
