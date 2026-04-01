"""Scripts for creating the bundled extension wheels (not version-controlled) from `requirements.txt`.

Wheel preparation may also update `blender_manifest.toml`, which is version-controlled.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from soulstruct.havok.utilities.files import SOULSTRUCT_HAVOK_PATH
from soulstruct.logging_utils import setup
from soulstruct.utilities.files import SOULSTRUCT_PATH

setup(console_level="INFO")
_LOGGER = logging.getLogger("soulstruct.blender.prepare_extensions")

_IO_SOULSTRUCT_SOURCE_DIR = Path(__file__).parent / "io_soulstruct"


def read_requirements() -> list[str]:
    """Read `requirements.txt` file and return a list of `pip`-compatible requirements."""
    requirements_path = _IO_SOULSTRUCT_SOURCE_DIR / "requirements.txt"
    if not requirements_path.is_file():
        raise RuntimeError("Cannot find `io_soulstruct/requirements.txt`.")
    requirements = requirements_path.read_text()
    return [line.strip() for line in requirements.splitlines() if not line.strip().startswith("#")]


def update_wheels(use_local_soulstruct: bool = False):
    """Update wheels in `io_soulstruct/wheels`."""
    wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "wheels"
    temp_wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "temp_wheels"

    requirements = read_requirements()

    pip_wheel_cmd = [sys.executable, "-m", "pip", "wheel"]
    if use_local_soulstruct:
        # Get live package roots for wheels.
        soulstruct_root_path = SOULSTRUCT_PATH("../..")
        soulstruct_havok_root_path = SOULSTRUCT_HAVOK_PATH("../..")
        pip_wheel_cmd += [req for req in requirements if not req.startswith("soulstruct")]
        pip_wheel_cmd += [str(soulstruct_root_path), str(soulstruct_havok_root_path)]
    else:
        # Get `soulstruct` from PyPI.
        pip_wheel_cmd += requirements

    pip_wheel_cmd += ["-w", str(temp_wheels_dir)]
    _LOGGER.info(f"pip wheel cmd: {' '.join(pip_wheel_cmd)}")

    try:
        subprocess.check_output(pip_wheel_cmd)
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(
            f"Failed to collect wheels for `io_soulstruct` extension. "
            f"Ensure that `pip` is installed and available in your Python environment.\n"
            f"Error: {ex}"
        )
        return 1

    # Succeeded. Delete old `wheels_dir` and rename `temp_wheels_dir`.
    wheels_dir.unlink(missing_ok=True)
    temp_wheels_dir.rename(wheels_dir)

    return 0

def update_blender_manifest_wheels():
    """Update Blender manifest from all 'wheels'."""
    wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "wheels"
    requirements = read_requirements()

    manifest_path = _IO_SOULSTRUCT_SOURCE_DIR / "blender_manifest.toml"
    if not manifest_path.is_file():
        raise RuntimeError("Cannot find `blender_manifest.toml`.")
    manifest_lines = manifest_path.read_text().splitlines()
    try:
        wheels_start_line_index = manifest_lines.index("# WHEELS START")
        wheels_end_line_index = manifest_lines.index("# WHEELS END")
    except ValueError:
        raise RuntimeError("Cannot find '# WHEELS START' and/or '# WHEELS END' lines in `blender_manifest.toml`.")

    wheel_lines = ["wheels = ["]
    for wheel_file in sorted(wheels_dir.glob("*.whl"), key=lambda p: p.name.lower()):
        wheel_lines.append(f"  \"./wheels/{wheel_file.name}\",")
        for req in requirements:
            if wheel_file.name.startswith(req.split("==")[0]):
                wheel_lines[-1] = wheel_lines[-1] + "  # TOP-LEVEL"
                break
    wheel_lines.append("]")

    new_manifest = manifest_lines[:wheels_start_line_index + 1] + wheel_lines + manifest_lines[wheels_end_line_index:]

    _LOGGER.info("Manifest wheels: " + ", ".join(wheel_lines))


    # Write new manifest.
    manifest_path.write_text("\n".join(new_manifest))

    _LOGGER.info("Successfully updated `io_soulstruct/wheels` and updated `io_soulstrlct/blender_manifest.toml`.")

    return 0


def blender_extension_build():
    """Use `blender.exe` to build the Soulstruct extension for Blender."""

    # Move into `io_soulstruct` directory.
    current_dir = Path.cwd()
    os.chdir(_IO_SOULSTRUCT_SOURCE_DIR)

    blender_cmd = [
        "blender", "--command", "extension", "build"
    ]

    _LOGGER.info(f"blender cmd: {' '.join(blender_cmd)}")
    try:
        subprocess.check_output(blender_cmd)
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(f"Failed to build `blender` extension. Error: {ex}")
        os.chdir(current_dir)
        return 1

    _LOGGER.info("Successfully built extension with `blender` command.")

    os.chdir(current_dir)
    return 0


def main():

    # update_wheels(use_local_soulstruct=True)
    # update_blender_manifest_wheels()
    blender_extension_build()


if __name__ == '__main__':
    main()
