import logging
from pathlib import Path

from soulstruct._logging import _ModuleFormatter, _ColoredModuleFormatter, CONSOLE_HANDLER, FILE_HANDLER


try:
    import colorama
except ImportError:
    colorama = None
else:
    colorama.just_fix_windows_console()


# Create new formatters for the sublogger with a different base_module_name.
IO_CONSOLE_FORMATTER = _ColoredModuleFormatter(
    base_module_name="io_soulstruct",
    fmt="$COLOR{levelname:>7} :: {modulepath:<40} :: {lineno:>4d} :: {message}$RESET",
    style="{",
    use_color=bool(colorama),
)
IO_FILE_FORMATTER = _ModuleFormatter(
    base_module_name="io_soulstruct",
    fmt="{levelname:>7} :: {asctime} :: {pathname:<35} :: Line {lineno:>4d} :: {message}",
    style="{",
)

_IO_LOGGER = logging.getLogger("soulstruct.io")
_IO_LOGGER.propagate = False  # don't use parent handlers

IO_CONSOLE_HANDLER = logging.StreamHandler()
IO_CONSOLE_HANDLER.setFormatter(IO_CONSOLE_FORMATTER)
IO_CONSOLE_HANDLER.setLevel(CONSOLE_HANDLER.level)
_IO_LOGGER.addHandler(IO_CONSOLE_HANDLER)

# TODO: Not using file handler while I need to hot-reload the module with Blender open.
# IO_LOG_PATH = str(Path(__file__).parent / "io_soulstruct.log")
# IO_FILE_HANDLER = logging.FileHandler(IO_LOG_PATH, mode="w", encoding="shift_jis_2004")
# IO_FILE_HANDLER.setFormatter(IO_FILE_FORMATTER)
# IO_FILE_HANDLER.setLevel(FILE_HANDLER.level)
# _IO_LOGGER.addHandler(IO_FILE_HANDLER)
