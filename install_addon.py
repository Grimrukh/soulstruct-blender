"""Install FLVER import/export scripts into Blender, along with Soulstruct.

The Blender script (`io_flver.py`) will ensure that the mini-Soulstruct module is added to the Blender path. Note that
you will have to restart Blender to see any changes to this mini-module, as `Reload Scripts` in Blender will not
re-import it.
"""
import shutil
import sys
from pathlib import Path

from soulstruct.utilities.files import PACKAGE_PATH


SCRIPT_FILES = (
    "__init__.py",
    "core.py",
    "export_flver.py",
    "import_flver.py",
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
        # Full Soulstruct install, now that Blender 3.0 supports Python 3.9.
        shutil.rmtree(blender_scripts_dir / "modules/soulstruct", ignore_errors=True)
        shutil.copytree(PACKAGE_PATH(), blender_scripts_dir / "modules/soulstruct")

    # Install actual Blender script.
    (blender_scripts_dir / "addons/io_flver").mkdir(exist_ok=True, parents=True)
    for script_path in SCRIPT_FILES:
        shutil.copy2(
            Path(__file__).parent / f"io_flver/{script_path}",
            blender_scripts_dir / f"addons/io_flver/{script_path}",
        )

    print(f"Blender FLVER `io_flver` installed to '{blender_scripts_dir}'.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(
            f"INVALID ARGUMENTS: {sys.argv}\n"
            f"Usage: `python install_blender_addon.py [blender_scripts_directory]`"
        )
        exit()
    install(sys.argv[1])
