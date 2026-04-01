"""Scripts for directly installing the extension and/or `soulstruct` into Blender.

Useful for live development.
"""

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from soulstruct.havok.utilities.files import SOULSTRUCT_HAVOK_PATH
from soulstruct.logging_utils import setup
from soulstruct.utilities.files import SOULSTRUCT_PATH

setup(console_level="INFO")
_LOGGER = logging.getLogger("soulstruct.blender.install_extension")

_ALWAYS_IGNORE = [
    "__pycache__", "*.pyc", ".git", ".idea", "*.egg-info", "tests",
    "soulstruct_config.json", "soulstruct.log",
]

_IO_SOULSTRUCT_SOURCE_DIR = Path(__file__).parent / "io_soulstruct"


def read_requirements() -> list[str]:
    """Read `requirements.txt` file and return a list of `pip`-compatible requirements."""
    requirements_path = _IO_SOULSTRUCT_SOURCE_DIR / "requirements.txt"
    if not requirements_path.is_file():
        raise RuntimeError("Cannot find `io_soulstruct/requirements.txt`.")
    requirements = requirements_path.read_text()
    return [line.strip() for line in requirements.splitlines() if not line.strip().startswith("#")]


def direct_install_addon(bl_version: str = "5.1", is_install_from_disk: bool = True):
    """Replace add-on package directly in AppData extensions for given Blender version."""

    if not _IO_SOULSTRUCT_SOURCE_DIR.is_dir():
        _LOGGER.error("Cannot find `io_soulstruct` next to script.")
        return 1

    # Is extension installed from disk or from Blender's Extensions platform?
    user = "user_default" if is_install_from_disk else "blender_org"

    io_soulstruct_dest_dir = Path(
        f"~/AppData/Roaming/Blender Foundation/Blender/{bl_version}/extensions/{user}/io_soulstruct"
    ).expanduser()
    if not io_soulstruct_dest_dir.is_dir():
        _LOGGER.error(
            f"`io_soulstruct` has not yet been installed at: {io_soulstruct_dest_dir}. "
            f"Do a proper initial installation first from Blender preferences (Add-ons)."
        )
        return 1

    # Copy add-on directory into extensions directly.
    ignore_patterns = shutil.ignore_patterns(*_ALWAYS_IGNORE)

    shutil.rmtree(io_soulstruct_dest_dir, ignore_errors=False)
    shutil.copytree(
        _IO_SOULSTRUCT_SOURCE_DIR,
        io_soulstruct_dest_dir,
        ignore=ignore_patterns,
    )
    _LOGGER.info(f"Blender addon `io_soulstruct` installed to '{io_soulstruct_dest_dir.parent}'.")
    return 0


def direct_install_soulstruct(
    bl_version: str = "5.1",
    use_local: bool = False,
    editable: bool = False,
) -> int:
    """Install `soulstruct` and `soulstruct-havok` directly into the '.local' site-packages for Blender."""

    if not use_local and editable:
        raise ValueError("Cannot use `editable` mode without `use_local`.")

    if bl_version >= "5.1":
        py_ver = "python3.13"
    else:
        py_ver = "python3.11"

    local_site_packages = Path(
        f"~/AppData/Roaming/Blender Foundation/Blender/{bl_version}/extensions/.local/lib/{py_ver}/site-packages"
    ).expanduser()
    if not local_site_packages.is_dir():
        _LOGGER.error(
            f"Could not find local site-packages at: {local_site_packages}. "
            f"Do a proper initial installation first from Blender preferences (Add-ons)."
        )
        return 1

    pip_cmd = [
        sys.executable, "-m", "pip", "install",
        "--upgrade",
        "--disable-pip-version-check",
        "--no-input",
        "--target", str(local_site_packages),
    ]
    requirements = read_requirements()

    # Three modes of direct installation:
    #   - install from PyPI
    #   - install from local (standard)
    #   - install from local (editable)

    if not use_local:
        pip_cmd += requirements
        # Done.
    else:
        # Install non-Soulstruct pinned requirements from PyPI (e.g. specific SciPy version).
        pip_cmd += [req for req in requirements if not req.startswith("soulstruct")]
        # Get live package roots for editable installation.
        soulstruct_root_path = SOULSTRUCT_PATH("../..")
        soulstruct_havok_root_path = SOULSTRUCT_HAVOK_PATH("../..")
        if editable:
            pip_cmd += ["-e", str(soulstruct_root_path), "-e", str(soulstruct_havok_root_path)]
        else:
            pip_cmd += [str(soulstruct_root_path), str(soulstruct_havok_root_path)]

    _LOGGER.info(f"pip cmd: {pip_cmd}")
    try:
        subprocess.check_output(pip_cmd)
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(f"Failed to `pip` install Soulstruct directly. Error: {ex}")
        return 1

    _LOGGER.info("Successfully `pip` installed Soulstruct directory.")
    return 0


PARSER = argparse.ArgumentParser(
    description="Install Soulstruct Blender extension directly and (optionally) Soulstruct modules.",
)
PARSER.add_argument("blenderVersion", help="Blender version, e.g. 5.1")
PARSER.add_argument("--installSoulstruct", action="store_true", help="Also install Soulstruct modules.")
PARSER.add_argument("-e", "--editable", action="store_true",
                    help="Install Soulstruct modules in editable mode from current environment.")


def main(args):

    parsed = PARSER.parse_args(args)

    direct_install_addon(parsed.blenderVersion, is_install_from_disk=True)

    if parsed.installSoulstruct:
        direct_install_soulstruct(bl_version=parsed.blenderVersion, use_local=True, editable=parsed.editable)


if __name__ == '__main__':
    main(sys.argv[1:])
