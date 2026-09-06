"""Scripts for preparing bundled wheels for the extension from `requirements.txt`, updating the version-controlled
`blender_manifest.toml`, and building the Blender extension zip.
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
_LOGGER = logging.getLogger("soulstruct.blender.prepare_extensions")

_IO_SOULSTRUCT_SOURCE_DIR = Path(__file__).parent / "io_soulstruct"
_RELEASES_DIR = Path(__file__).parent / "Releases"


def read_requirements() -> list[str]:
    """Read `requirements.txt` file and return a list of `pip`-compatible requirements."""
    requirements_path = _IO_SOULSTRUCT_SOURCE_DIR / "requirements.txt"
    if not requirements_path.is_file():
        raise RuntimeError("Cannot find `io_soulstruct/requirements.txt`.")
    requirements = requirements_path.read_text()
    return [line.strip() for line in requirements.splitlines() if not line.strip().startswith("#")]


def update_wheels(
    firelink_source_dir: Path,
    use_local_soulstruct: bool = False,
    no_build_isolation: bool = False,
):
    """Update wheels in `io_soulstruct/wheels`."""
    wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "wheels"
    temp_wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "temp_wheels"

    # The 'requirements.txt' file contains pinned requirements for:
    #   - soulstruct
    #   - soulstruct-havok
    #   - pyrelink
    # Other requirements (numpy, rich, etc.) are transitive through these pinned versions.
    # The PyPI package names for the above will be replaced by local folders according to args.
    requirements = read_requirements()

    pip_wheel_cmd = [sys.executable, "-m", "pip", "wheel"]
    if no_build_isolation:
        pip_wheel_cmd += ["--no-build-isolation"]

    if use_local_soulstruct:
        # Get live package roots for wheels (e.g. for testing unreleased development versions).
        soulstruct_root_path = SOULSTRUCT_PATH("../..")
        if not soulstruct_root_path.is_dir():
            raise RuntimeError(f"Not a local soulstruct directory: {soulstruct_root_path}")
        if not (soulstruct_root_path / "pyproject.toml").is_file():
            raise RuntimeError(f"Not a local soulstruct directory (missing `pyproject.toml`): {soulstruct_root_path}")

        soulstruct_havok_root_path = SOULSTRUCT_HAVOK_PATH("../..")
        if not soulstruct_havok_root_path.is_dir():
            raise RuntimeError(f"Not a local soulstruct-havok directory {soulstruct_havok_root_path}")
        if not (soulstruct_havok_root_path / "pyproject.toml").is_file():
            raise RuntimeError(f"Not a local soulstruct-havok directory (missing `pyproject.toml`): {soulstruct_havok_root_path}")

        pip_wheel_cmd += [str(soulstruct_root_path), str(soulstruct_havok_root_path)]
        requirements = [req for req in requirements if not req.startswith("soulstruct")]

    if firelink_source_dir:
        pip_wheel_cmd += [str(firelink_source_dir)]
        requirements = [req for req in requirements if not req.startswith("pyrelink")]

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
    if wheels_dir.exists():
        shutil.rmtree(wheels_dir)
    temp_wheels_dir.rename(wheels_dir)

    _LOGGER.info("Successfully updated `io_soulstruct/wheels`.")

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

    _LOGGER.info("Manifest wheels: " + "".join(wheel_lines))

    # Write new manifest.
    manifest_path.write_text("\n".join(new_manifest))

    _LOGGER.info("Successfully updated `io_soulstruct/blender_manifest.toml`.")

    return 0


def blender_extension_build():
    """Use `blender.exe` to build the Soulstruct extension for Blender.

    NOTE: The `blender` command requires any current installed add-ons, including Soulstruct, to run without issues.
    """

    # Move into `io_soulstruct` directory.
    current_dir = Path.cwd()
    os.chdir(_IO_SOULSTRUCT_SOURCE_DIR)

    # Make Releases directory if it doesn't exist.
    _RELEASES_DIR.mkdir(parents=True, exist_ok=True)

    blender_cmd = [
        "blender", "--command", "extension", "build", "--output-dir", str(_RELEASES_DIR),
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


PARSER = argparse.ArgumentParser()
PARSER.add_argument(
    "--update-wheels", action="store_true", default=False,
    help="Whether to update the wheels directory or not (default: False)."
)
PARSER.add_argument(
    "--build-extension", action="store_true", default=True,
    help="Whether to build the Blender extension ZIP package or not (default: True)."
)
PARSER.add_argument(
    "--firelink-source-dir",
    type=Path,
    default=None,
    help="Path to the Firelink source directory (for pyrelink build). "
         "If not provided, `pyrelink` will be found on PyPI.",
)
PARSER.add_argument(
    "--no-build-isolation",
    action="store_true",
    default=False,
    help="Do not use build isolation when building wheels from source. "
         "This makes rebuilds faster in C++. You must have `scikit-build-core` and `pybind11` "
         "installed in your local environment.",
)


def main():

    args = PARSER.parse_args()

    if args.update_wheels:
        update_wheels(
            firelink_source_dir=args.firelink_source_dir,
            use_local_soulstruct=True,
            no_build_isolation=args.no_build_isolation,
        )
        update_blender_manifest_wheels()

    if args.build_extension:
        blender_extension_build()


if __name__ == '__main__':
    main()
