"""Copy scripts and `soulstruct` modules to a release path, then zip it up."""
import logging
import typing as tp
from importlib import import_module
from fnmatch import fnmatch
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from soulstruct.logging_utils import setup
from soulstruct.utilities.files import SOULSTRUCT_PATH
from soulstruct.havok.utilities.files import SOULSTRUCT_HAVOK_PATH

setup(console_level="INFO")
_LOGGER = logging.getLogger("soulstruct.blender.bundle_addon_release")

_ALWAYS_IGNORE = [
    "__pycache__/*", "*.pyc", ".git/*", ".idea/*", "*.egg-info/*", "tests/*",
    "soulstruct_config.json", "soulstruct.log",
]


def zip_map(
    zip_path: str | Path,
    *mappings: tuple[Path | str, Path | str],
    ignore: tp.Callable[[Path | str], bool] | tp.Iterable[str] | None = None,
):
    """
    Build *zip_path* from multiple (SOURCE, DEST_PREFIX) mappings.

    Parameters
    ----------
    zip_path : str | Path
        Destination archive; “.zip” is appended if missing.
    *mappings : tuple[path-like, str]
        (source_path, dest_prefix) pairs.
    ignore : Callable[[Path, str], bool] | Iterable[str] | None
        - If callable: `ignore(src_path, rel_path)` -> True to skip.
        - If iterable of glob patterns: any pattern match skips the file.
        - None disables filtering (default).

    Example
    -------
    zip_map(
        "bundle.zip",
        ("io_soulstruct", ""),                    # root of zip
        ("io_soulstruct_lib/soulstruct", "libs"),
        ("io_soulstruct_lib/soulstruct-havok", "libs"),
        ignore=("__pycache__", "*.pyc", "*.pyd"), # skip caches/bytecode
    )
    """
    # normalise ignore to a function
    if ignore is None:
        def _ignored(_src, _rel):
            return False
    elif callable(ignore):
        _ignored = ignore
    else:
        patterns = tuple(ignore)
        def _ignored(_src, _rel):
            return any(
                fnmatch(_rel, pat) or fnmatch(_src.name, pat)
                for pat in patterns
            )

    zip_path = Path(zip_path).with_suffix(".zip")

    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        for src, prefix in mappings:
            src = Path(src)
            if not src.exists():
                raise FileNotFoundError(src)
            base = src if src.is_dir() else src.parent

            for path in ([src] if src.is_file() else src.rglob("*")):
                if path.is_dir():
                    continue
                rel = path.relative_to(base).as_posix()
                if _ignored(path, rel):
                    continue

                arcname = (Path(prefix) / rel).as_posix()
                zf.write(path, arcname)


def get_version() -> str:

    # Path to the add-on root (directory that contains version.py)
    addon_root = Path(__file__).parent / "io_soulstruct"
    spec = import_module("importlib.util").spec_from_file_location(
        "io_soulstruct_version", addon_root / "version.py"
    )
    version_mod = import_module("importlib.util").module_from_spec(spec)
    spec.loader.exec_module(version_mod)  # type: ignore[attr-defined]

    return version_mod.__version__  # e.g. "0.9.3"


def zip_addon_release():
    """Just copy current `io_soulstruct` and `io_soulstruct_lib` into `release_dir`."""

    this_dir = Path(__file__).parent
    version = get_version()

    zip_path = this_dir / f"Releases/io_soulstruct-{version}.zip"
    if zip_path.exists():
        _LOGGER.warning(f"Replacing existing zip: '{zip_path}'")
        zip_path.unlink()

    src_io_soulstruct_dir = this_dir / "io_soulstruct"
    soulstruct_root_path = SOULSTRUCT_PATH("../..")
    havok_root_path = SOULSTRUCT_HAVOK_PATH("../..")  # step out of `src/soulstruct` (in `soulstruct-havok`)

    zip_path.parent.mkdir(parents=True, exist_ok=True)

    _LOGGER.info(f"Creating release zip at: {zip_path}")
    zip_map(
        zip_path,
        (src_io_soulstruct_dir, "io_soulstruct"),
        (soulstruct_root_path, "io_soulstruct_lib/soulstruct"),
        (havok_root_path, "io_soulstruct_lib/soulstruct-havok"),
        ignore=_ALWAYS_IGNORE,
    )
    _LOGGER.info(f"Release created: {zip_path}")


def main():
    zip_addon_release()


if __name__ == '__main__':
    main()
