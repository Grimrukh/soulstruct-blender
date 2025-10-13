"""Install all scripts into Blender, along with `soulstruct`, `soulstruct-havok`, and required third-party modules."""
import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from soulstruct.logging_utils import setup
from soulstruct.utilities.files import SOULSTRUCT_PATH
from soulstruct.havok.utilities.files import SOULSTRUCT_HAVOK_PATH

setup(console_level="INFO")
_LOGGER = logging.getLogger("soulstruct.blender.install_addon")

_ALWAYS_IGNORE = [
    "__pycache__", "*.pyc", ".git", ".idea", "*.egg-info", "tests",
    "soulstruct_config.json", "soulstruct.log",
]


def install_addon(
    addons_dir: str | Path,
    install_soulstruct=True,
    editable_soulstruct=False,
    refresh_only: bool | None = None,
):
    """Copy `io_soulstruct` and (by default) `io_soulstruct_lib` into given `addons_dir` parent directory."""

    addons_dir = Path(addons_dir)

    this_dir = Path(__file__).parent
    src_io_soulstruct_dir = this_dir / "io_soulstruct"

    dest_io_soulstruct_dir = addons_dir / "io_soulstruct"
    dest_io_soulstruct_lib_dir = addons_dir / "io_soulstruct_lib"
    dest_modules_dir = addons_dir / "modules"

    ignore_patterns = shutil.ignore_patterns(*_ALWAYS_IGNORE)

    # Install actual Blender scripts.
    if dest_io_soulstruct_dir.is_dir():
        shutil.rmtree(dest_io_soulstruct_dir, ignore_errors=False)
    shutil.copytree(
        src_io_soulstruct_dir,
        dest_io_soulstruct_dir,
        ignore=ignore_patterns,
    )
    _LOGGER.info(f"Blender addon `io_soulstruct` installed to '{addons_dir}'.")

    if not install_soulstruct:
        return  # done, just installing Blender scripts

    # Full Soulstruct install.

    # Two modes: an editable install pointing to THIS environment's `soulstruct` and `soulstruct-havok` modules, or
    # copying the modules from the package into `io_soulstruct_lib` and performing an editable install from there.
    # (The latter is what the add-on will attempt to do itself if it detects that the modules are not installed.)

    soulstruct_root_path = SOULSTRUCT_PATH("../..")  # step out of `src/soulstruct`
    havok_root_path = SOULSTRUCT_HAVOK_PATH("../..")  # step out of `src/soulstruct` (in `soulstruct-havok`)

    if editable_soulstruct:
        # Get the current environment's `soulstruct` and `soulstruct-havok` module paths.
        _LOGGER.info("Installing Soulstruct modules in editable mode...")
        soulstruct_install_path = soulstruct_root_path
        havok_install_path = havok_root_path
    else:
        _LOGGER.info("Copying Soulstruct modules to `io_soulstruct_lib`...")
        soulstruct_install_path = dest_io_soulstruct_lib_dir / "soulstruct"
        shutil.rmtree(soulstruct_install_path, ignore_errors=True)
        _LOGGER.info("Copying Soulstruct module...")
        shutil.copytree(
            soulstruct_root_path,
            soulstruct_install_path,
            # NOTE: this is the container of `src`, not the package itself
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(*_ALWAYS_IGNORE, "oo2core_6_win64.dll"),  # handled manually
        )

        # Copy over `oo2core_6_win64.dll` if it exists and isn't already in destination folder.
        # (It may already be in use by Blender.)
        oo2core_dll = SOULSTRUCT_PATH("oo2core_6_win64.dll")
        if oo2core_dll.is_file() and not (
            soulstruct_install_path / "src/soulstruct/oo2core_6_win64.dll").is_file():
            shutil.copy(oo2core_dll, dest_io_soulstruct_lib_dir / "soulstruct/src/soulstruct")

        _LOGGER.info("Copying Soulstruct-Havok module...")
        havok_install_path = dest_io_soulstruct_lib_dir / "soulstruct-havok"
        shutil.rmtree(havok_install_path, ignore_errors=True)
        # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
        shutil.copytree(
            havok_root_path,
            havok_install_path,
            ignore=ignore_patterns,
            dirs_exist_ok=True,
        )

    if refresh_only is None:
        soulstruct_pths = dest_modules_dir.glob("modules/*soulstruct*.pth")
        refresh_only = bool(list(soulstruct_pths))
    if refresh_only:
        # No need to call `pip` below (we assume dependencies are already installed and point to correct paths).
        _LOGGER.info("Refreshing Soulstruct module paths only (no pip install).")
        return

    try:
        subprocess.run(
            [
                sys.executable, "-m", "pip", "install",
                "-e", str(soulstruct_install_path),
                "-e", str(havok_install_path),
                "--target", str(dest_modules_dir),
                "--exists-action", "i",
                "--upgrade-strategy", "only-if-needed",
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(
            f"Failed to install Soulstruct modules in editable mode. "
            f"Ensure that `pip` is installed and available in your Python environment.\n"
            f"Error: {ex}"
        )


PARSER = argparse.ArgumentParser(
    description="Install Soulstruct Blender add-on and (optionally) Soulstruct modules.",
)
PARSER.add_argument("addonsDirectory", help="Path to Blender's `addons` directory.")
PARSER.add_argument("--installSoulstruct", action="store_true", help="Also install Soulstruct modules.")
PARSER.add_argument("-e", "--editable", action="store_true",
                    help="Install Soulstruct modules in editable mode (pointing to current environment).")
PARSER.add_argument("-r", "--refreshOnly", action="store_true", default=None,
                    help="Refresh the Soulstruct modules only; do not run `pip` or install dependencies. "
                         "Defaults to `true` if any files 'modules/*soulstruct*.pth' exist in `addons_directory`.")


def main(args):

    parsed = PARSER.parse_args(args)

    install_addon(
        parsed.addonsDirectory,
        install_soulstruct=parsed.installSoulstruct,
        editable_soulstruct=parsed.editable,
        refresh_only=parsed.refreshOnly,
    )


if __name__ == '__main__':
    main(sys.argv[1:])
