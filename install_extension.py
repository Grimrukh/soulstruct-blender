"""Scripts for directly installing the extension and/or `soulstruct` into Blender.

Modes:
  --inject-extension     Copy extension source directly into Blender AppData extensions (dev).
  --inject-soulstruct    Inject soulstruct/soulstruct-havok source into Blender site-packages (dev, no pip).
  --install-pyrelink     Pip-install pyrelink from a local Firelink source dir into Blender site-packages.
  --install-from-zip     Use `blender.exe` to install a built extension .zip (production testing).
"""

import argparse
import logging
import os
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
    "soulstruct_config.json", "soulstruct.log", "*.blend1",
]

_IO_SOULSTRUCT_SOURCE_DIR = Path(__file__).parent / "io_soulstruct"


# ---- Helpers -------------------------------------------------------------------------

def _get_py_ver(bl_version: str) -> str:
    return "python3.13" if bl_version >= "5.2" else "python3.11"


def _get_local_site_packages(bl_version: str) -> Path:
    py_ver = _get_py_ver(bl_version)
    return Path(
        f"~/AppData/Roaming/Blender Foundation/Blender/{bl_version}"
        f"/extensions/.local/lib/{py_ver}/site-packages"
    ).expanduser()


def _get_extension_dir(bl_version: str, is_install_from_disk: bool = True) -> Path:
    user = "user_default" if is_install_from_disk else "blender_org"
    return Path(
        f"~/AppData/Roaming/Blender Foundation/Blender/{bl_version}/extensions/{user}/io_soulstruct"
    ).expanduser()


# ---- Install actions -----------------------------------------------------------------

def inject_extension(bl_version: str = "5.2", is_install_from_disk: bool = True) -> int:
    """Copy extension source directly into Blender AppData extensions (dev mode)."""
    if not _IO_SOULSTRUCT_SOURCE_DIR.is_dir():
        _LOGGER.error("Cannot find `io_soulstruct` next to script.")
        return 1

    dest_dir = _get_extension_dir(bl_version, is_install_from_disk)
    if not dest_dir.is_dir():
        _LOGGER.error(
            f"`io_soulstruct` is not yet installed at: {dest_dir}. "
            f"Do a proper initial installation first from Blender preferences (Extensions)."
        )
        return 1

    shutil.rmtree(dest_dir)
    shutil.copytree(_IO_SOULSTRUCT_SOURCE_DIR, dest_dir, ignore=shutil.ignore_patterns(*_ALWAYS_IGNORE))
    _LOGGER.info(f"Installed `io_soulstruct` to '{dest_dir}'.")
    return 0


def inject_soulstruct(bl_version: str = "5.2") -> int:
    """Inject soulstruct + soulstruct-havok source directly into Blender's .local site-packages (no pip).

    Preserves any .dll files already present (e.g. `oo2core`) in case Blender is running.
    """
    local_site_packages = _get_local_site_packages(bl_version)
    if not local_site_packages.is_dir():
        _LOGGER.error(f"Could not find local site-packages at: {local_site_packages}.")
        return 1

    soulstruct_dir = local_site_packages / "soulstruct"

    if soulstruct_dir.is_dir():
        # Delete everything except root-level DLLs (which may be locked by Blender).
        for entry in os.scandir(soulstruct_dir):
            if entry.is_file() and entry.name.lower().endswith(".dll"):
                continue
            if entry.is_file():
                os.remove(entry.path)
            elif entry.is_dir():
                shutil.rmtree(entry.path)

    # Ignore `oo2core` DLL if already present; otherwise, copy in as normal.
    if (soulstruct_dir / "oo2core_6_win64.dll").is_file():
        ignore_patterns = shutil.ignore_patterns(*_ALWAYS_IGNORE, "oo2core_6_win64.dll")
    else:
        ignore_patterns = shutil.ignore_patterns(*_ALWAYS_IGNORE)

    # Copy `soulstruct` base library.
    shutil.copytree(
        SOULSTRUCT_PATH(),
        soulstruct_dir,
        dirs_exist_ok=True,
        ignore=ignore_patterns,
    )
    _LOGGER.info(f"Copied 'soulstruct' into Blender site-packages: {soulstruct_dir}")
    # Copy `soulstruct.havok`.
    shutil.copytree(
        SOULSTRUCT_HAVOK_PATH("havok"),
        soulstruct_dir / "havok",
        dirs_exist_ok=False,
        ignore=ignore_patterns,
    )
    _LOGGER.info(f"Copied 'soulstruct.havok' into Blender site-packages: {soulstruct_dir / 'havok'}")
    return 0


def pip_install_pyrelink(
    firelink_source_dir: Path,
    bl_version: str = "5.2",
    no_build_isolation: bool = False,
) -> int:
    """Pip-install pyrelink from a local Firelink source directory into Blender's .local site-packages."""
    if not firelink_source_dir or not firelink_source_dir.is_dir():
        _LOGGER.error(f"Invalid Firelink source directory: {firelink_source_dir}")
        return 1

    local_site_packages = _get_local_site_packages(bl_version)
    if not local_site_packages.is_dir():
        _LOGGER.error(f"Could not find local site-packages at: {local_site_packages}.")
        return 1

    pip_cmd = [
        sys.executable, "-m", "pip", "install",
        "--upgrade",
        "--disable-pip-version-check",
        "--no-input",
        "--no-build-isolation",  # re-use cached build results when possible
        "--target", str(local_site_packages),
        str(firelink_source_dir),
    ]
    if no_build_isolation:
        pip_cmd.append("--no-build-isolation")

    _LOGGER.info(f"pip cmd: {' '.join(pip_cmd)}")
    try:
        completed_process = subprocess.run(pip_cmd, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(f"Failed to pip-install pyrelink. Error: {ex}")
        return 1
    if completed_process.returncode != 0:
        _LOGGER.error(f"Command to pip-install pyrelink returned {completed_process.returncode}.")

    _LOGGER.info("Successfully installed pyrelink into Blender site-packages.")
    return 0


def blender_install_extension(zip_path: Path, bl_version: str = "5.2") -> int:
    """Use `blender.exe` to install a built extension .zip (production test mode).

    Equivalent to installing from disk via Blender's Extensions preferences.
    Updates the bundled wheels in Blender's .local site-packages.
    """
    if not zip_path.is_file():
        _LOGGER.error(f"Extension zip not found: {zip_path}")
        return 1

    blender_cmd = [
        "blender", "--command", "extension", "install-file",
        "--enable",
        "--repo", "user_default",
        str(zip_path),
    ]
    _LOGGER.info(f"blender cmd: {' '.join(blender_cmd)}")
    try:
        subprocess.check_output(blender_cmd)
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(f"Failed to install extension via blender. Error: {ex}")
        return 1

    _LOGGER.info(f"Successfully installed extension from '{zip_path.name}' via blender.")
    return 0


# ---- CLI -----------------------------------------------------------------------------

PARSER = argparse.ArgumentParser(
    description="Install the Soulstruct Blender extension and/or Python modules.",
)
PARSER.add_argument(
    "blenderversion",
    help="Blender version to install into, e.g. '5.2'",
)
PARSER.add_argument(
    "--inject-extension", action="store_true", default=True,
    help="Copy extension source directly into Blender AppData extensions (dev mode).",
)
PARSER.add_argument(
    "--inject-soulstruct", action="store_true", default=False,
    help="Inject soulstruct/soulstruct-havok source directly into Blender site-packages (dev mode, no pip).",
)
PARSER.add_argument(
    "--install-pyrelink", action="store_true", default=False,
    help="Pip-install pyrelink from local Firelink source into Blender site-packages.",
)
PARSER.add_argument(
    "--firelink-source-dir", type=Path, default=None,
    help="Path to Firelink source directory (required for --install-pyrelink).",
)
PARSER.add_argument(
    "--no-build-isolation", action="store_true", default=False,
    help="Disable pip build isolation when installing pyrelink (faster C++ rebuilds; "
         "requires scikit-build-core and pybind11 to be installed locally).",
)
PARSER.add_argument(
    "--install-from-zip", type=Path, default=None, metavar="ZIP",
    help="Path to a built extension .zip. Uses blender.exe to install it properly (production test mode).",
)


def main(args):
    parsed = PARSER.parse_args(args)

    if parsed.inject_extension:
        if result := inject_extension(parsed.blenderversion):
            return result

    if parsed.inject_soulstruct:
        if result := inject_soulstruct(parsed.blenderversion):
            return result

    if parsed.install_pyrelink:
        if not parsed.firelink_source_dir:
            _LOGGER.error("--install-pyrelink requires --firelink-source-dir.")
            return 1
        if result := pip_install_pyrelink(
            firelink_source_dir=parsed.firelink_source_dir,
            bl_version=parsed.blenderversion,
            no_build_isolation=parsed.no_build_isolation,
        ):
            return result

    if parsed.install_from_zip:
        if result := blender_install_extension(parsed.install_from_zip, parsed.blenderversion):
            return result

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
