"""Install all scripts into Blender, along with Soulstruct.

The Blender script (`io_flver.py`) will ensure that the mini-Soulstruct module is added to the Blender path. Note that
you will have to restart Blender to see any changes to this mini-module, as `Reload Scripts` in Blender will not
re-import it.
"""
import json
import shutil
import sys
from pathlib import Path

from soulstruct.utilities.files import PACKAGE_PATH

from soulstruct_havok.utilities.files import HAVOK_PACKAGE_PATH


def install(blender_scripts_dir: str | Path, update_soulstruct_module=False, update_third_party_modules=False):
    """`blender_scripts_dir` should be the `scripts` folder in a specific version of Blender inside your AppData.

    For example:
        `install(Path("~/AppData/Roaming/Blender/2.93/scripts").expanduser())`
    """
    blender_scripts_dir = Path(blender_scripts_dir)
    if blender_scripts_dir.name != "scripts":
        raise ValueError(
            f"Expected Blender install directory to be called 'scripts'. Given path: {blender_scripts_dir}"
        )

    this_dir = Path(__file__).parent
    blender_addons_dir = blender_scripts_dir / "addons"
    addon_dir = blender_addons_dir / "io_soulstruct"
    addon_dir.mkdir(exist_ok=True, parents=True)
    modules_dir = addon_dir / "modules"

    # Install actual Blender scripts.
    settings_path = addon_dir / "GlobalSettings.json"
    if settings_path.is_file():
        settings_data = settings_path.read_bytes()
    else:
        # Default settings.
        settings_data = json.dumps(
            {
                "GameDirectory": "",
                "PNGCacheDirectory": "D:\\blender_png_cache",
            }, indent=4
        ).encode()
    shutil.rmtree(addon_dir, ignore_errors=True)
    shutil.copytree(this_dir / "io_soulstruct", addon_dir)
    settings_path.write_bytes(settings_data)
    print(f"# Blender addon `io_soulstruct` installed to '{blender_addons_dir}'.")

    if update_soulstruct_module:
        # Full Soulstruct install, now that Blender 3.3 supports Python 3.10.
        print("# Installing Soulstruct module into Blender...")
        shutil.rmtree(modules_dir / "soulstruct", ignore_errors=True)
        # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
        shutil.copytree(
            PACKAGE_PATH(),
            modules_dir / "soulstruct",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "oo2core_6_win64.dll"),
        )

        # Copy over `oo2core_6_win64.dll` if it exists and isn't already in destination folder.
        oo2core_dll = PACKAGE_PATH("oo2core_6_win64.dll")
        if oo2core_dll.is_file() and not (modules_dir / "soulstruct/oo2core_6_win64.dll").is_file():
            shutil.copy(oo2core_dll, modules_dir / "soulstruct")

        if HAVOK_PACKAGE_PATH is not None:
            print("# Installing Soulstruct-Havok module into Blender...")
            shutil.rmtree(modules_dir / "soulstruct_havok", ignore_errors=True)
            # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
            shutil.copytree(HAVOK_PACKAGE_PATH(), modules_dir / "soulstruct_havok", dirs_exist_ok=True)

        if update_third_party_modules:
            install_site_package("colorama", modules_dir / "colorama")
            install_site_package("scipy", modules_dir / "scipy")
            install_site_package("scipy.libs", modules_dir / "scipy.libs")


def install_site_package(dir_name: str, destination_dir: Path):
    exe_path = Path(sys.executable)
    site_packages_dir = exe_path.parent / "Lib/site-packages"
    if not site_packages_dir.is_dir():  # exe could be in `Scripts` subfolder (venv)
        site_packages_dir = exe_path.parent / "../Lib/site-packages"
        if not site_packages_dir.is_dir():
            raise FileNotFoundError(f"Could not find site-packages directory for Python executable: {exe_path}.")
    package_dir = site_packages_dir / dir_name
    if not package_dir.is_dir():
        raise FileNotFoundError(f"Could not find site-package directory: {package_dir}.")
    print(f"# Installing site-package `{dir_name}` into Blender...")
    shutil.copytree(package_dir, destination_dir, dirs_exist_ok=True)


def main(args):
    match args:
        case [blender_scripts_directory, "--updateSoulstruct", "--updateThirdParty"]:
            install(blender_scripts_directory, update_soulstruct_module=True, update_third_party_modules=True)
        case [blender_scripts_directory, "--updateSoulstruct"]:
            install(blender_scripts_directory, update_soulstruct_module=True)
        case [blender_scripts_directory, "--updateThirdParty"]:
            install(blender_scripts_directory, update_third_party_modules=True)
        case [blender_scripts_directory]:
            install(blender_scripts_directory, update_soulstruct_module=False)
        case _:
            print(
                f"INVALID ARGUMENTS: {sys.argv}\n"
                f"Usage: `python install_addon.py [blender_scripts_directory] "
                f"[--updateSoulstruct] [--updateThirdParty]`"
            )


if __name__ == '__main__':
    main(sys.argv[1:])
