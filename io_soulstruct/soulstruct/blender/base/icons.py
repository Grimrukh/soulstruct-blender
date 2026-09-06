"""Custom branded icons for Soulstruct Panels, loaded once at add-on registration.

Icons live in `io_soulstruct/icons/<name>.png` (a sibling of the `soulstruct` package, alongside `wheels/`), and
are loaded into a single `bpy.utils.previews` collection here. `get_icon_id()` is the only thing other modules
need to call; `bpy_base.panel.SoulstructPanel` uses it automatically for panel header icons, so most code in this
add-on never needs to import this module directly.
"""
from __future__ import annotations

__all__ = [
    "get_icon_id",
]

from pathlib import Path

import bpy
import bpy.utils.previews

from .register import io_soulstruct_register, io_soulstruct_unregister

# Names must match `io_soulstruct/icons/<name>.png` file stems.
_ICON_NAMES = (
    "general",
    "flver",
    "msb",
    "navmesh",
    "nav_graph",
    "animation",
    "collision",
    "cutscene",
    "misc",
    "dds",
)

# Set at registration; cleared at unregistration (tolerates 'Reload Scripts').
_icon_collection: bpy.utils.previews.ImagePreviewCollection | None = None


@io_soulstruct_register
def _load_icons():
    global _icon_collection
    _icon_collection = bpy.utils.previews.new()
    # `base/icons.py` -> `soulstruct/blender/base/` -> up three levels -> add-on root -> `icons/`.
    icons_dir = Path(__file__).parents[3] / "icons"
    for name in _ICON_NAMES:
        png_path = icons_dir / f"{name}.png"
        if png_path.is_file():
            _icon_collection.load(name, str(png_path), "IMAGE")


@io_soulstruct_unregister
def _unload_icons():
    global _icon_collection
    if _icon_collection is not None:
        bpy.utils.previews.remove(_icon_collection)
        _icon_collection = None


def get_icon_id(name: str) -> int:
    """Return the custom `icon_value` ID for icon `name`, or 0 (Blender's 'no icon') if unavailable."""
    if _icon_collection is None or name not in _icon_collection:
        return 0
    return _icon_collection[name].icon_id
