"""Manually extracts the `bl_info['version']` key from the add-on module (which we can't import without `"""
__all__ = [
    "__version_tuple__",
    "__version__",
]

import ast
import re
from pathlib import Path

_init_str = (Path(__file__).parent / "__init__.py").read_text()
_version_re = re.search(r"\n +\"version\": (\(\d+, \d+, \d+\)),\n", _init_str)

__version_tuple__ = ast.literal_eval(_version_re.group(1))
__version__ = ".".join(map(str, __version_tuple__))
