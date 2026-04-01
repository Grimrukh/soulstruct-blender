"""Install all scripts into Blender, along with `soulstruct`, `soulstruct-havok`, and required third-party modules."""
import argparse
import importlib
import importlib.util
import logging
import os
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

_IO_SOULSTRUCT_SOURCE_DIR = Path(__file__).parent / "io_soulstruct"


def update_wheels():
    """Update wheels in `io_soulstruct/wheels`."""
    wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "wheels"
    temp_wheels_dir = _IO_SOULSTRUCT_SOURCE_DIR / "temp_wheels"

    requirements_path = _IO_SOULSTRUCT_SOURCE_DIR / "requirements.txt"
    if not requirements_path.is_file():
        raise RuntimeError("Cannot find `io_soulstruct/requirements.txt`.")
    requirements = requirements_path.read_text()

    manifest_path = _IO_SOULSTRUCT_SOURCE_DIR / "blender_manifest.toml"
    if not manifest_path.is_file():
        raise RuntimeError("Cannot find `blender_manifest.toml`.")
    manifest_lines = manifest_path.read_text().splitlines()
    try:
        wheels_start_line_index = manifest_lines.index("# WHEELS START")
        wheels_end_line_index = manifest_lines.index("# WHEELS END")
    except ValueError:
        raise RuntimeError("Cannot find '# WHEELS START' and/or '# WHEELS END' lines in `blender_manifest.toml`.")

    pip_wheel_args = []

    for line in requirements.splitlines():
        if line.strip().startswith("#"):
            continue  # comment
        # Every line in `requirements.txt` can be fed directly to `pip`.
        pip_wheel_args.append(line)

    pip_wheel_cmd = [sys.executable, "-m", "pip", "wheel", *pip_wheel_args, "-w", str(temp_wheels_dir)]
    _LOGGER.info(f"pip wheel cmd: {' '.join(pip_wheel_cmd)}")

    try:
        subprocess.run(
            pip_wheel_cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(
            f"Failed to collect wheels for `io_soulstruct` extension. "
            f"Ensure that `pip` is installed and available in your Python environment.\n"
            f"Error: {ex}"
        )
        return 1

    # Update Blender manifest.
    wheel_lines = [
        f"./wheels/{wheel_file.name}"
        for wheel_file in sorted(temp_wheels_dir.glob("*.whl"), key=lambda p: p.name.lower())
    ]
    new_manifest = manifest_lines[:wheels_start_line_index + 1] + wheel_lines + manifest_lines[wheels_end_line_index:]

    # Succeeded. Delete old `wheels_dir` and rename `temp_wheels_dir`.
    wheels_dir.unlink(missing_ok=True)
    temp_wheels_dir.rename(wheels_dir)

    # Write new manifest.
    manifest_path.write_text("".join(new_manifest))

    return 0


def blender_extension_build():

    # Move into `io_soulstruct` directory.
    current_dir = Path.cwd()
    os.chdir(_IO_SOULSTRUCT_SOURCE_DIR)

    blender_cmd = [
        "blender", "--command", "extension", "build"
    ]

    try:
        subprocess.check_output(blender_cmd)
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(f"Failed to build `blender` extension. Error: {ex}")
        os.chdir(current_dir)
        return 1

    os.chdir(current_dir)
    return 0


def direct_install_addon(bl_version: str = "5.1", user: str = "user_default"):
    """Replace add-on package directly in AppData extensions for given Blender version."""

    if not _IO_SOULSTRUCT_SOURCE_DIR.is_dir():
        _LOGGER.error("Cannot find `io_soulstruct` next to script.")
        return 1

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


def direct_install_soulstruct(bl_version: str = "5.1") -> int:
    """Install `soulstruct` and `soulstruct-havok` directly into the '.local' site-packages for Blender."""

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

    # TODO: Build soulstruct wheels? Or try to circumvent that step? Editable install?


def install_addon(
    addons_dir: str | Path,
    install_soulstruct=True,
    use_current_soulstruct=False,
) -> int:
    """Copy `io_soulstruct` and (by default) `io_soulstruct_lib` into given `addons_dir` parent directory."""

    addons_dir = Path(addons_dir)

    this_dir = Path(__file__).parent
    src_io_soulstruct_dir = this_dir / "io_soulstruct"

    dest_io_soulstruct_dir = addons_dir / "io_soulstruct"
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
        return 0  # done, just installing Blender scripts

    # Full Soulstruct install.

    # Two modes: an editable install pointing to THIS environment's `soulstruct` and `soulstruct-havok` modules, or
    # doing a full Soulstruct pip install from PyPI.

    soulstruct_root_path = SOULSTRUCT_PATH("../..")  # step out of `src/soulstruct`
    havok_root_path = SOULSTRUCT_HAVOK_PATH("../..")  # step out of `src/soulstruct` (in `soulstruct-havok`)

    pip_cmd = [
        sys.executable, "-m", "pip", "install",
        "scipy==1.16.3",  # TODO: locking version until 1.17.1 read-only array bug fixed
    ]

    if use_current_soulstruct:
        # Get the current environment's `soulstruct` and `soulstruct-havok` module paths.

        # Verify versions match.
        from soulstruct.version import __version__ as editable_soulstruct_version
        if editable_soulstruct_version != required_soulstruct_version:
            raise RuntimeError(
                f"Cannot do an editable install of `soulstruct` version {editable_soulstruct_version}. "
                f"Required version for `io_soulstruct` is {required_soulstruct_version}."
            )

        from soulstruct.havok.version import __version__ as editable_soulstruct_havok_version
        if editable_soulstruct_havok_version != required_soulstruct_havok_version:
            raise RuntimeError(
                f"Cannot do an editable install of `soulstruct-havok` version {editable_soulstruct_havok_version}. "
                f"Required version for `io_soulstruct` is {required_soulstruct_havok_version}."
            )

        _LOGGER.info("Installing Soulstruct modules in editable mode...")
        soulstruct_install_path = soulstruct_root_path
        havok_install_path = havok_root_path
        pip_cmd += [
            "-e", str(soulstruct_install_path),
            "-e", str(havok_install_path),
        ]
    else:
        # Pip-install Soulstruct. Read required versions from addon `__init__.py`.

        _LOGGER.info("Pip-installing Soulstruct modules to `addons/modules`...")
        pip_cmd += [
            f"soulstruct=={required_soulstruct_version}",
            f"soulstruct-havok=={required_soulstruct_havok_version}",
        ]

    pip_cmd += [
        "--target", str(dest_modules_dir),
        "--exists-action", "i",
        "--upgrade",
        "--disable-pip-version-check",
        "--no-input",
        "--retries", "10",
        "--timeout", "60",
    ]

    _LOGGER.info(f"pip cmd: {pip_cmd}")

    try:
        subprocess.run(
            pip_cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    except subprocess.CalledProcessError as ex:
        _LOGGER.error(
            f"Failed to install Soulstruct modules in editable mode. "
            f"Ensure that `pip` is installed and available in your Python environment.\n"
            f"Error: {ex}"
        )
        return 1

    return 0

PARSER = argparse.ArgumentParser(
    description="Install Soulstruct Blender add-on and (optionally) Soulstruct modules.",
)
PARSER.add_argument("addonsDirectory", help="Path to Blender's `addons` directory.")
PARSER.add_argument("--installSoulstruct", action="store_true", help="Also install Soulstruct modules.")
PARSER.add_argument("-e", "--editable", action="store_true",
                    help="Install Soulstruct modules in editable mode (pointing to current environment).")


def main(args):

    parsed = PARSER.parse_args(args)

    install_addon(
        parsed.addonsDirectory,
        install_soulstruct=parsed.installSoulstruct,
        use_current_soulstruct=parsed.editable,
    )


if __name__ == '__main__':
    main(sys.argv[1:])
