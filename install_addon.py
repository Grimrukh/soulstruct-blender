"""Install all scripts into Blender, along with Soulstruct.

The Blender script (`io_flver.py`) will ensure that the mini-Soulstruct module is added to the Blender path. Note that
you will have to restart Blender to see any changes to this mini-module, as `Reload Scripts` in Blender will not
re-import it.
"""
import shutil
import sys
from pathlib import Path

from soulstruct.utilities.files import PACKAGE_PATH

from soulstruct_havok.utilities.files import HAVOK_PACKAGE_PATH


PY_SITE_PACKAGES = Path(sys.executable).parent / "../Lib/site-packages"


def copy_addon(addons_dir: str | Path, copy_soulstruct_module=True, copy_third_party_modules=True, clear_settings=True):
    """Copy `io_soulstruct` and (by default) `io_soulstruct_lib` into given `addons_dir` parent directory."""

    addons_dir = Path(addons_dir)

    this_dir = Path(__file__).parent
    src_io_soulstruct_dir = this_dir / "io_soulstruct"

    dest_io_soulstruct_dir = addons_dir / "io_soulstruct"
    dest_io_soulstruct_lib_dir = addons_dir / "io_soulstruct_lib"

    ignore_pycache = shutil.ignore_patterns("__pycache__", "*.pyc", "__address_cache__")

    # Install actual Blender scripts, preserving existing 'SoulstructSettings.json' only.
    settings_path = dest_io_soulstruct_dir / "SoulstructSettings.json"
    settings_data = settings_path.read_bytes() if not clear_settings and settings_path.is_file() else b""
    if dest_io_soulstruct_dir.is_dir():
        shutil.rmtree(dest_io_soulstruct_dir, ignore_errors=False)
    shutil.copytree(
        src_io_soulstruct_dir,
        dest_io_soulstruct_dir,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "__address_cache__", "soulstruct_config.json", "soulstruct.log"
        ),
    )
    if settings_data:
        settings_path.write_bytes(settings_data)
    print(f"# Blender addon `io_soulstruct` installed to '{addons_dir}'.")

    if copy_soulstruct_module:
        # Full Soulstruct install, now that Blender 3.3 supports Python 3.10.
        print("# Copying Soulstruct module...")
        shutil.rmtree(dest_io_soulstruct_lib_dir / "soulstruct", ignore_errors=True)
        # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
        shutil.copytree(
            PACKAGE_PATH(),
            dest_io_soulstruct_lib_dir / "soulstruct",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "oo2core_6_win64.dll"),
        )

        # Copy over `oo2core_6_win64.dll` if it exists and isn't already in destination folder.
        oo2core_dll = PACKAGE_PATH("oo2core_6_win64.dll")
        if oo2core_dll.is_file() and not (dest_io_soulstruct_lib_dir / "soulstruct/oo2core_6_win64.dll").is_file():
            shutil.copy(oo2core_dll, dest_io_soulstruct_lib_dir / "soulstruct")

        if HAVOK_PACKAGE_PATH is not None:
            print("# Copying Soulstruct-Havok module...")
            shutil.rmtree(dest_io_soulstruct_lib_dir / "soulstruct_havok", ignore_errors=True)
            # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
            shutil.copytree(
                HAVOK_PACKAGE_PATH(),
                dest_io_soulstruct_lib_dir / "soulstruct_havok",
                ignore=ignore_pycache,
                dirs_exist_ok=True,
            )

    if copy_third_party_modules:
        # NOTE: Blender already comes with `numpy`.
        copy_site_package("colorama", dest_io_soulstruct_lib_dir / "colorama")
        copy_site_package("constrata", dest_io_soulstruct_lib_dir / "constrata")
        copy_site_package("scipy", dest_io_soulstruct_lib_dir / "scipy")
        copy_site_package("scipy.libs", dest_io_soulstruct_lib_dir / "scipy.libs")


def install(blender_addons_dir: str | Path, update_soulstruct_module=False, update_third_party_modules=False):
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

    copy_addon(blender_addons_dir, update_soulstruct_module, update_third_party_modules, clear_settings=False)


def copy_site_package(dir_name: str, destination_dir: Path):
    """Blender 4.1 onwards requires Python 3.11 versions."""
    if not PY_SITE_PACKAGES.is_dir():
        raise FileNotFoundError(f"Could not find site-packages directory: {PY_SITE_PACKAGES}.")
    package_dir = PY_SITE_PACKAGES / dir_name
    if not package_dir.is_dir():
        raise FileNotFoundError(f"Could not find site-package directory: {package_dir}.")
    print(f"# Copying site-package '{dir_name}'...")
    shutil.copytree(
        package_dir,
        destination_dir,
        ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
        dirs_exist_ok=True,
    )


def main(args):
    match args:
        case [release_directory, "--release"]:
            # This is just a copy, not a local Blender install.
            copy_addon(release_directory, copy_soulstruct_module=True, copy_third_party_modules=True)
        case [addons_directory, "--updateSoulstruct", "--updateThirdParty"]:
            install(addons_directory, update_soulstruct_module=True, update_third_party_modules=True)
        case [addons_directory, "--updateSoulstruct"]:
            install(addons_directory, update_soulstruct_module=True)
        case [addons_directory, "--updateThirdParty"]:
            install(addons_directory, update_third_party_modules=True)
        case [addons_directory]:
            install(addons_directory, update_soulstruct_module=False)
        case _:
            print(
                f"INVALID ARGUMENTS: {sys.argv}\n"
                f"Usage: `python install_addon.py [addons_directory] "
                f"[--release] [--updateSoulstruct] [--updateThirdParty]`"
            )


if __name__ == '__main__':
    main(sys.argv[1:])
