"""Install all scripts into Blender, along with `soulstruct`, `soulstruct-havok`, and required third-party modules."""
import logging
import shutil
import sys
from pathlib import Path

from soulstruct.utilities.files import PACKAGE_PATH
from soulstruct.havok.utilities.files import HAVOK_PACKAGE_PATH

_LOGGER = logging.getLogger("soulstruct.blender.install_addon")


# TODO: Option to install using editable CURRENT soulstruct/soulstruct-havok modules, rather than copying them.


# We take third-party modules from our current Python site-packages directory.
PY_SITE_PACKAGES = Path(sys.executable).parent / "../Lib/site-packages"


def copy_addon(addons_dir: str | Path, copy_soulstruct_module=True):
    """Copy `io_soulstruct` and (by default) `io_soulstruct_lib` into given `addons_dir` parent directory."""

    addons_dir = Path(addons_dir)

    this_dir = Path(__file__).parent
    src_io_soulstruct_dir = this_dir / "io_soulstruct"

    dest_io_soulstruct_dir = addons_dir / "io_soulstruct"
    dest_io_soulstruct_lib_dir = addons_dir / "io_soulstruct_lib"

    ignore_patterns = shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".git", ".idea", "soulstruct_config.json", "soulstruct.log"
    )

    # Install actual Blender scripts.
    if dest_io_soulstruct_dir.is_dir():
        shutil.rmtree(dest_io_soulstruct_dir, ignore_errors=False)
    shutil.copytree(
        src_io_soulstruct_dir,
        dest_io_soulstruct_dir,
        ignore=ignore_patterns,
    )
    _LOGGER.info(f"Blender addon `io_soulstruct` installed to '{addons_dir}'.")

    if copy_soulstruct_module:
        # Full Soulstruct install.
        _LOGGER.info("Copying Soulstruct module...")
        shutil.rmtree(dest_io_soulstruct_lib_dir / "soulstruct", ignore_errors=True)
        # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
        shutil.copytree(
            PACKAGE_PATH("../.."),
            dest_io_soulstruct_lib_dir / "soulstruct",  # NOTE: this is the container of `src`, not the package itself
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".git", ".idea", "soulstruct_config.json", "soulstruct.log",
                "oo2core_6_win64.dll",  # handled manually below
            ),
        )

        # Copy over `oo2core_6_win64.dll` if it exists and isn't already in destination folder.
        # (It may already be in use by Blender.)
        oo2core_dll = PACKAGE_PATH("oo2core_6_win64.dll")
        if oo2core_dll.is_file() and not (dest_io_soulstruct_lib_dir / "soulstruct/src/soulstruct/oo2core_6_win64.dll").is_file():
            shutil.copy(oo2core_dll, dest_io_soulstruct_lib_dir / "soulstruct/src/soulstruct")

        _LOGGER.info("Copying Soulstruct-Havok module...")
        shutil.rmtree(dest_io_soulstruct_lib_dir / "soulstruct-havok", ignore_errors=True)
        # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
        shutil.copytree(
            HAVOK_PACKAGE_PATH("../../.."),
            dest_io_soulstruct_lib_dir / "soulstruct-havok",
            ignore=ignore_patterns,
            dirs_exist_ok=True,
        )


def install(blender_addons_dir: str | Path, update_soulstruct_module=False):
    """Install add-on to a real Blender scripts directory, with optional updating of bundled libraries.

    `blender_scripts_dir` should be the `scripts` folder in a specific version of Blender inside your AppData.

    For example:
        `install(Path("~/AppData/Roaming/Blender/4.2/scripts").expanduser())`
    """
    blender_addons_dir = Path(blender_addons_dir)
    if blender_addons_dir.name != "addons":
        raise ValueError(
            f"Expected Blender install directory to be called 'addons'. Given path: {blender_addons_dir}"
        )
    if blender_addons_dir.parent.name != "scripts":
        raise ValueError(
            f"Expected Blender install directory to be inside parent 'scripts'. Given path: {blender_addons_dir}"
        )

    blender_addons_dir.mkdir(exist_ok=True, parents=True)

    copy_addon(blender_addons_dir, update_soulstruct_module)


def main(args):
    match args:
        case [release_directory, "--release"]:
            # This is just a copy, not a local Blender install.
            copy_addon(release_directory, copy_soulstruct_module=True)
        case [addons_directory, "--updateSoulstruct"]:
            install(addons_directory, update_soulstruct_module=True)
        case [addons_directory]:
            install(addons_directory, update_soulstruct_module=False)
        case _:
            _LOGGER.error(
                f"INVALID ARGUMENTS: {sys.argv}\n"
                f"Usage: `python install_addon.py [addons_directory] "
                f"[--release] [--updateSoulstruct]`"
            )


if __name__ == '__main__':
    main(sys.argv[1:])
