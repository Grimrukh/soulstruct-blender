"""Install all scripts into Blender, along with Soulstruct.

The Blender script (`io_flver.py`) will ensure that the mini-Soulstruct module is added to the Blender path. Note that
you will have to restart Blender to see any changes to this mini-module, as `Reload Scripts` in Blender will not
re-import it.
"""
import shutil
import sys
from pathlib import Path

from soulstruct.utilities.files import PACKAGE_PATH


ADDON_MODULES = (
    "io_flver",
)


def install(blender_scripts_dir: str | Path, update_soulstruct_module=False):
    """`blender_scripts_dir` should be the `scripts` folder in a specific version of Blender inside your AppData.

    For example:
        `install(Path("~/AppData/Roaming/Blender/2.93/scripts").expanduser())`
    """
    blender_scripts_dir = Path(blender_scripts_dir)
    if blender_scripts_dir.name != "scripts":
        raise ValueError(
            f"Expected Blender install directory to be called 'scripts'. Given path: {blender_scripts_dir}"
        )

    if update_soulstruct_module:
        # Full Soulstruct install, now that Blender 3.3 supports Python 3.10.
        print("# Installing Soulstruct module into Blender...")
        shutil.rmtree(blender_scripts_dir / "modules/soulstruct", ignore_errors=True)
        # Removal may not be complete if Blender is open, particularly as `soulstruct.log` may not be deleted.
        shutil.copytree(PACKAGE_PATH(), blender_scripts_dir / "modules/soulstruct", dirs_exist_ok=True)

    # Install actual Blender scripts.
    this_dir = Path(__file__).parent
    blender_addons_dir = blender_scripts_dir / "addons"
    for addon_module_name in ADDON_MODULES:
        blender_module_dir = blender_addons_dir / addon_module_name
        blender_module_dir.mkdir(exist_ok=True, parents=True)
        shutil.rmtree(blender_module_dir, ignore_errors=True)
        shutil.copytree(this_dir / addon_module_name, blender_module_dir)
        print(f"# Blender addon `{addon_module_name}` installed to '{blender_addons_dir}'.")


def main(args):
    match args:
        case [blender_scripts_directory, "--updateSoulstruct"]:
            install(blender_scripts_directory, update_soulstruct_module=True)
        case [blender_scripts_directory]:
            install(blender_scripts_directory, update_soulstruct_module=False)
        case _:
            print(
                f"INVALID ARGUMENTS: {sys.argv}\n"
                f"Usage: `python install_addon.py [blender_scripts_directory] [--updateSoulstruct]`"
            )


if __name__ == '__main__':
    main(sys.argv[1:])
