import logging

from soulstruct._logging import _ModuleFormatter, _ColoredModuleFormatter


try:
    import colorama
except ImportError:
    colorama = None
else:
    colorama.just_fix_windows_console()


_IO_LOGGER = logging.getLogger("soulstruct.io")
_IO_LOGGER.propagate = False  # don't use parent handlers

IO_CONSOLE_FORMATTER: _ColoredModuleFormatter | None = None
IO_FILE_FORMATTER: _ModuleFormatter | None = None
IO_CONSOLE_HANDLER: logging.StreamHandler | None = None
IO_FILE_HANDLER: logging.StreamHandler | None = None


def _set_up_logging():
    global IO_CONSOLE_FORMATTER, IO_FILE_FORMATTER, IO_CONSOLE_HANDLER, IO_FILE_HANDLER

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

    IO_CONSOLE_HANDLER = logging.StreamHandler()
    IO_CONSOLE_HANDLER.setFormatter(IO_CONSOLE_FORMATTER)
    IO_CONSOLE_HANDLER.setLevel(logging.INFO)
    _IO_LOGGER.addHandler(IO_CONSOLE_HANDLER)

    # io_log_path = str(Path(__file__).parent / "io_soulstruct.log")
    # IO_FILE_HANDLER = logging.FileHandler(io_log_path, mode="w", encoding="shift_jis_2004")
    # IO_FILE_HANDLER.setFormatter(IO_FILE_FORMATTER)
    # IO_FILE_HANDLER.setLevel(logging.INFO)
    # TODO: Not using file handler while I need to hot-reload the module with Blender open (opened log file can't be
    #  deleted for re-install while Blender is open).
    # _IO_LOGGER.addHandler(IO_FILE_HANDLER)


def _get_existing_references():
    global IO_CONSOLE_FORMATTER, IO_FILE_FORMATTER, IO_CONSOLE_HANDLER, IO_FILE_HANDLER
    IO_CONSOLE_HANDLER = next(
        (handler for handler in _IO_LOGGER.handlers if isinstance(handler, logging.StreamHandler)), None
    )
    IO_CONSOLE_FORMATTER = IO_CONSOLE_HANDLER.formatter if IO_CONSOLE_HANDLER else None
    IO_FILE_HANDLER = next(
        (handler for handler in _IO_LOGGER.handlers if isinstance(handler, logging.FileHandler)), None
    )
    IO_FILE_FORMATTER = IO_FILE_HANDLER.formatter if IO_FILE_HANDLER else None


if not _IO_LOGGER.hasHandlers():
    # Only set up once (e.g. not every time we reload Blender scripts).
    _set_up_logging()
    _IO_LOGGER.info("Set up logging for 'io_soulstruct' sublogger.")
else:
    # Re-assign global variables to existing formatters/handlers.
    _get_existing_references()
    _IO_LOGGER.info("Logger 'io_soulstruct' already set up.")
