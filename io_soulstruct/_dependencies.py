"""Dependency manifest and installation function for `io_soulstruct` Blender add-on."""

__all__ = [
    "REQUIREMENTS",
    "clean_stale_blender_module_paths",
    "ensure_soulstruct_installed_in_blender",
]

import importlib
import re
import site
import subprocess
import sys


REQUIREMENTS = {
    "scipy": "1.16.3",  # TODO: locking old version until 1.17.x 'read-only array' bug fixed in Rotation
    "soulstruct": "2.3.2",
    "soulstruct-havok": "1.2.1",
}


def clean_stale_blender_module_paths():
    """Remove `sys.path` entries that point to a *different* Blender version's `addons/modules` directory.

    Without this, an older soulstruct installed under e.g. Blender 5.0's appdata could shadow the version
    required by the current Blender version, causing `_ensure_soulstruct_installed` to see a stale install.
    """

    try:
        import bpy
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Must have `bpy` available to call this function.")

    current_blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
    # Matches paths like: .../Blender Foundation/Blender/5.0/scripts/addons/modules
    blender_version_re = re.compile(r"[/\\]Blender[/\\](\d+\.\d+)[/\\]", re.IGNORECASE)

    paths_to_remove = []
    for path_str in list(sys.path):
        m = blender_version_re.search(path_str)
        if m and m.group(1) != current_blender_version and "addons" in path_str.lower():
            paths_to_remove.append(path_str)

    for path_str in paths_to_remove:
        sys.path.remove(path_str)
        print(f"[Soulstruct] Removed stale Blender module path from sys.path: {path_str}")

    # Flush any already-imported soulstruct modules so they can be re-imported from the correct location.
    stale_modules = [name for name in sys.modules if name == "soulstruct" or name.startswith("soulstruct.")]
    for name in stale_modules:
        del sys.modules[name]
    if stale_modules:
        print(f"[Soulstruct] Flushed {len(stale_modules)} stale soulstruct module(s) from sys.modules.")


def ensure_soulstruct_installed_in_blender():
    """Verify that the correct versions of `soulstruct` and `soulstruct-havok` are installed.

    If the required versions are already present (regular *or* editable install), this is a no-op.
    Otherwise, the function will attempt to pip-install from PyPI.
    """

    try:
        import bpy
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Must have `bpy` available to call this function.")

    user_addon_modules = bpy.utils.user_resource("SCRIPTS", path="addons/modules")

    needs_install = False

    try:
        import soulstruct.version
    except ModuleNotFoundError:
        needs_install = True
        print(f"[Soulstruct] Package `soulstruct` is not installed (need {REQUIREMENTS['soulstruct']}).")
    else:
        installed_soulstruct_version = soulstruct.version.__version__
        if installed_soulstruct_version != REQUIREMENTS["soulstruct"]:
            print(
                f"[Soulstruct] Package `soulstruct` version {installed_soulstruct_version} is installed, "
                f"but version {REQUIREMENTS['soulstruct']} is required by this add-on."
            )
            needs_install = True
        else:
            print(f"[Soulstruct] Package `soulstruct` {installed_soulstruct_version} is installed -- OK")

    try:
        import soulstruct.havok.version
    except ModuleNotFoundError:
        needs_install = True
        print(f"[Soulstruct] Package `soulstruct-havok` is not installed (need {REQUIREMENTS['soulstruct-havok']}).")
    else:
        installed_soulstruct_havok_version = soulstruct.havok.version.__version__
        if installed_soulstruct_havok_version != REQUIREMENTS["soulstruct-havok"]:
            print(
                f"[Soulstruct] Package `soulstruct-havok` version {installed_soulstruct_havok_version} is installed, "
                f"but version {REQUIREMENTS['soulstruct-havok']} is required by this add-on."
            )
            needs_install = True
        else:
            print(f"[Soulstruct] Package `soulstruct-havok` {installed_soulstruct_havok_version} is installed -- OK")

    if not needs_install:
        return  # all good

    # --- Install / upgrade required packages. ---

    def _call_python_module(purpose: str, *args: str):
        try:
            subprocess.run([sys.executable, "-m", *args], stdout=sys.stdout, stderr=sys.stderr, check=True)
        except subprocess.CalledProcessError as _ex:
            print(_ex.stdout)
            print(_ex.stderr)
            raise RuntimeError(f"Failed to {purpose} in Blender Python. Error: {_ex}") from _ex

    _call_python_module("call `ensurepip`", "ensurepip")
    _call_python_module("upgrade `pip`", "pip", "install", "--upgrade", "pip")

    pip_args = [f"{name}=={version}" for name, version in REQUIREMENTS.items()]
    print("[Soulstruct] Installing from PyPI ...")
    _call_python_module(
        "install `soulstruct` and `soulstruct-havok` from PyPI",
        "pip", "install",
            *pip_args,
            "--target", user_addon_modules,
            "--upgrade",
    )

    print("[Soulstruct] pip install complete. Refreshing paths ...")

    # Refresh so newly installed packages are discoverable.
    site.addsitedir(user_addon_modules)
    # Required for Blender import machinery to re-check 'addons/modules' directory.
    importlib.invalidate_caches()

    # Verify the key sub-packages are actually importable.
    try:
        import soulstruct.version
        import soulstruct.havok.version
    except ImportError as ex:
        raise ImportError(
            "Required modules 'soulstruct' and 'soulstruct-havok' could not be imported, even after installation. "
            "Please ensure they are installed in Blender's Python environment (in user's local `modules`). "
            "Restarting Blender and trying again may also fix this."
        ) from ex
