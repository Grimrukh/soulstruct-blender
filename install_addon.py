"""Install all scripts into Blender, along with `soulstruct`, `soulstruct-havok`, and required third-party modules."""
import argparse
import importlib
import importlib.util
import logging
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


    # Import 'io_soulstruct/_dependencies.py' module directly (no addon '__init__.py').
    dep_spec = importlib.util.spec_from_file_location(
        "io_soulstruct._dependencies", Path(__file__).parent / "io_soulstruct" / "_dependencies.py"
    )
    dep_module = importlib.util.module_from_spec(dep_spec)
    dep_spec.loader.exec_module(dep_module)

    # Get required versions of Soulstruct.
    required_soulstruct_version = dep_module.REQUIREMENTS["soulstruct"]
    print(f"Required `soulstruct` version: {required_soulstruct_version}")
    required_soulstruct_havok_version = dep_module.REQUIREMENTS["soulstruct-havok"]
    print(f"Required `soulstruct-havok` version: {required_soulstruct_havok_version}")

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
