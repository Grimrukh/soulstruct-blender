#!/usr/bin/env python3
"""
split_bpy_types.py

Splits the large bpy/types.pyi stub file from the fake-bpy-module site package
into multiple smaller files organised under a bpy/types/ package, then
generates an __init__.pyi that re-exports everything. PyCharm can then index
each smaller file independently without hitting its file size limit.

The script auto-detects the bpy package location by importing it, so it must
be run with the same Python interpreter that has fake-bpy-module installed.

Usage:
    python split_bpy_types.py [--chunk-size N] [--undo]

Options:
    --chunk-size N   Max class definitions per output file (default: 50).
                     Decrease if PyCharm still struggles.
    --undo           Reverse a previous run: restore types/__init__.pyi from
                     _init.pyi and delete the generated chunk files.

Extra stubs (soulstruct_extra_stubs.py):
    If a file named soulstruct_extra_stubs.py exists next to this script,
    it is parsed for class definitions. Whenever a Blender type class is split
    out whose name matches one of those classes, the extra annotated attributes
    are injected at the top of the class body (after the class header line and
    any leading docstring). The extra stubs file's header (TYPE_CHECKING imports
    etc.) is also prepended to any chunk file that receives injections, so that
    the injected type names resolve correctly.

    The extra stubs file should contain only bare class definitions with
    annotated attributes -- no method bodies, no __init__, just annotations:

        class Scene:
            my_prop: MyPropType
            other_prop: OtherType

What it does:
    1. Imports bpy to locate the site-package directory.
    2. Reads bpy/types/__init__.pyi.
    3. Optionally loads soulstruct_extra_stubs.py from alongside this script.
    4. Writes chunked _chunk_NNN.pyi files into the existing bpy/types/ dir,
       injecting extra annotations into matching classes as it goes.
    5. Renames bpy/types/__init__.pyi -> bpy/types/_init.pyi so PyCharm
       ignores it (underscore-prefixed files are skipped by PyCharm's indexer)
       while the original is preserved for --undo.
    6. Writes a new bpy/types/__init__.pyi that re-exports from the chunks.
"""

import argparse
import ast
import math
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

# Target maximum number of top-level definitions per output file.
# Adjust downward if PyCharm still struggles.
CHUNK_SIZE = 50

# Prefix used for generated chunk filenames, e.g. _chunk_000.pyi
CHUNK_PREFIX = "_chunk_"

# Name of the optional extra stubs file to look for alongside this script.
EXTRA_STUBS_FILENAME = "soulstruct_extra_stubs.py"


# ---------------------------------------------------------------------------
# Extra stubs loading
# ---------------------------------------------------------------------------

class ExtraStubs:
    """
    Holds the parsed contents of soulstruct_extra_stubs.py.

    For each class defined in that file we store the raw annotation lines to
    inject (indented 4 spaces, ready to insert).

    We also capture the file's header lines (everything before the first class)
    to prepend to any chunk file that receives injections, ensuring the type
    names referenced in the annotations are importable.
    """

    def __init__(self, header_lines: list[str], classes: dict[str, list[str]]):
        # Lines to prepend to chunk files that receive injections (imports etc.)
        self.header_lines = header_lines
        # Map from class name -> list of annotation lines (with trailing newlines)
        self.classes = classes

    def get_injection(self, class_name: str) -> list[str] | None:
        """Return the annotation lines for class_name, or None if not present."""
        return self.classes.get(class_name)


def load_extra_stubs(path: Path) -> ExtraStubs | None:
    """
    Parse soulstruct_extra_stubs.py and return an ExtraStubs instance, or None
    if the file does not exist.
    """
    if not path.exists():
        return None

    print(f"[INFO] Loading extra stubs from {path}")
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(
            f"[WARN] Could not parse {path}: {exc} -- extra stubs will be ignored.",
            file=sys.stderr,
        )
        return None

    # Find the line number of the first class definition (0-based).
    first_class_line = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            first_class_line = node.lineno - 1  # 0-based
            break

    # Everything before the first class is the header (TYPE_CHECKING block etc.)
    header_lines = lines[:first_class_line] if first_class_line is not None else []

    # Extract annotations and inline comments from each top-level class,
    # preserving their original source order.
    classes: dict[str, list[str]] = {}

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        class_body_start = node.lineno       # 1-based, the 'class Foo:' line itself
        class_body_end = node.end_lineno     # 1-based inclusive

        # Collect (lineno, text) for annotations and comment-only lines,
        # then sort by line number to preserve interleaved comments.
        items: list[tuple[int, str]] = []

        # Annotated attributes from the AST.
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.AnnAssign):
                for lineno in range(child.lineno - 1, child.end_lineno):
                    items.append((lineno, "    " + lines[lineno].lstrip()))

        # Comment-only lines (AST doesn't represent these).
        for lineno in range(class_body_start, class_body_end):
            stripped = lines[lineno].strip()
            if stripped.startswith("#"):
                items.append((lineno, "    " + stripped + "\n"))

        # Sort by line number and deduplicate (multi-line annotations produce
        # one item per line from the range above).
        items.sort(key=lambda x: x[0])
        seen: set[int] = set()
        final_lines: list[str] = []
        for lineno, text in items:
            if lineno not in seen:
                seen.add(lineno)
                final_lines.append(text)

        if final_lines:
            classes[node.name] = final_lines
            print(f"[INFO]   Extra stubs: {node.name} ({len(final_lines)} lines)")

    return ExtraStubs(header_lines, classes)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_top_level_blocks(source: str) -> list[dict]:
    """
    Return a list of top-level blocks from the stub source.  Each block is:
        {
            "kind":  "class" | "assign" | "import" | "other",
            "name":  str | None,   # None for import/other blocks
            "lines": list[str],    # the raw source lines belonging to this block
            "start": int,          # 0-based line index in the original file
        }

    Strategy: use the AST for reliable class/assignment boundary detection,
    then map AST nodes back to raw source lines so we preserve comments and
    exact formatting.
    """
    lines = source.splitlines(keepends=True)

    # PEP 695 generic class syntax (class Foo[T]) was introduced in Python
    # 3.12. Older interpreters reject it as a SyntaxError. Since we only
    # use the AST for block boundary detection, strip the type parameter
    # list before parsing -- the class names and bodies are unaffected.
    parse_source = re.sub(r'(class\s+\w+)\[[^\]]*\]', r'\1', source)

    try:
        tree = ast.parse(parse_source)
    except SyntaxError as exc:
        print(f"[ERROR] Could not parse input file: {exc}", file=sys.stderr)
        sys.exit(1)

    # Build a sorted list of (start_lineno, end_lineno, node) for top-level nodes.
    # ast line numbers are 1-based.
    node_spans = []
    for node in ast.iter_child_nodes(tree):
        start = node.lineno - 1          # convert to 0-based
        end = node.end_lineno            # end_lineno is 1-based inclusive -> exclusive slice
        node_spans.append((start, end, node))

    node_spans.sort(key=lambda x: x[0])

    blocks = []
    prev_end = 0

    for start, end, node in node_spans:
        # Capture any leading blank lines / module-level comments that fall
        # between the previous block and this one as part of this block.
        effective_start = prev_end

        block_lines = lines[effective_start:end]
        prev_end = end

        if isinstance(node, ast.ClassDef):
            kind = "class"
            name = node.name
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            kind = "assign"
            # Best-effort name extraction
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id
            elif isinstance(node, ast.Assign) and node.targets:
                t = node.targets[0]
                name = t.id if isinstance(t, ast.Name) else None
            else:
                name = None
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            kind = "import"
            name = None
        else:
            kind = "other"
            name = None

        blocks.append({
            "kind": kind,
            "name": name,
            "lines": block_lines,
            "start": effective_start,
        })

    # Capture any trailing content after the last node
    if prev_end < len(lines):
        blocks.append({
            "kind": "other",
            "name": None,
            "lines": lines[prev_end:],
            "start": prev_end,
        })

    return blocks


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def inject_extra_annotations(block_lines: list[str], extra_lines: list[str]) -> list[str]:
    """
    Insert extra_lines into block_lines immediately after the class header line
    and any leading docstring, before the first existing member.

    Returns a new list of lines.
    """
    result = list(block_lines)

    # Step 1: find the class header line (first line matching 'class ...')
    header_idx = 0
    for i, line in enumerate(result):
        if re.match(r'\s*class\s+', line):
            header_idx = i
            break

    # Step 2: find where the class body starts (first non-blank line after header)
    body_start = header_idx + 1
    while body_start < len(result) and result[body_start].strip() == "":
        body_start += 1

    if body_start >= len(result):
        # Empty class body -- append at end
        insert_at = len(result)
    else:
        stripped = result[body_start].strip()

        # Step 3: skip past a leading docstring if present
        if stripped.startswith('"""') or stripped.startswith("'''"):
            quote = '"""' if stripped.startswith('"""') else "'''"
            rest = stripped[3:]
            if quote in rest:
                # Single-line docstring
                insert_at = body_start + 1
            else:
                # Multi-line docstring: scan for closing quotes
                insert_at = body_start + 1
                while insert_at < len(result):
                    if quote in result[insert_at]:
                        insert_at += 1
                        break
                    insert_at += 1
        else:
            # No docstring -- insert right at body start
            insert_at = body_start

    # Step 4: build injection block with a trailing blank line for readability
    injection = list(extra_lines)
    if injection and not injection[-1].endswith("\n"):
        injection[-1] += "\n"
    injection.append("\n")

    result[insert_at:insert_at] = injection
    return result


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def group_blocks_into_chunks(
    blocks: list[dict], chunk_size: int
) -> tuple[list[dict], list[list[dict]]]:
    """
    Returns:
        header_blocks  - import / module-level assignments to include in every chunk
        chunks         - list of lists of class/other blocks
    """
    header_blocks = []
    body_blocks = []

    for block in blocks:
        if block["kind"] in ("import", "assign") and not body_blocks:
            # Treat leading imports and module-level assignments as header material
            header_blocks.append(block)
        else:
            body_blocks.append(block)

    # Split body blocks into chunks of `chunk_size` class definitions each.
    # Non-class blocks are attached to the nearest preceding class chunk.
    chunks: list[list[dict]] = []
    current_chunk: list[dict] = []
    class_count = 0

    for block in body_blocks:
        current_chunk.append(block)
        if block["kind"] == "class":
            class_count += 1
            if class_count >= chunk_size:
                chunks.append(current_chunk)
                current_chunk = []
                class_count = 0

    if current_chunk:
        chunks.append(current_chunk)

    return header_blocks, chunks


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def write_chunk(
    path: Path,
    header_blocks: list[dict],
    chunk_blocks: list[dict],
    extra_stubs: "ExtraStubs | None" = None,
) -> list[str]:
    """
    Write a single chunk file and return the list of exported class names.

    If extra_stubs is provided and any class in this chunk has a matching entry,
    the extra annotations are injected into that class body, and the extra stubs
    header (TYPE_CHECKING imports etc.) is prepended to the file.
    """
    exported: list[str] = []

    # Determine which classes in this chunk have extra annotations, so we know
    # whether to prepend the extra stubs header to this file.
    injected_classes: set[str] = set()
    if extra_stubs:
        for block in chunk_blocks:
            if block["kind"] == "class" and block["name"] in extra_stubs.classes:
                injected_classes.add(block["name"])

    with path.open("w", encoding="utf-8") as fh:
        # Prepend the extra stubs header (TYPE_CHECKING block) if needed.
        if injected_classes and extra_stubs and extra_stubs.header_lines:
            fh.writelines(extra_stubs.header_lines)
            fh.write("\n")

        # Write the standard generated header (imports etc.)
        for block in header_blocks:
            fh.writelines(block["lines"])

        fh.write("\n")

        # Write class / other blocks, injecting extra annotations where needed.
        for block in chunk_blocks:
            if block["kind"] == "class" and block["name"] in injected_classes:
                injection = extra_stubs.get_injection(block["name"])
                merged_lines = inject_extra_annotations(block["lines"], injection)
                fh.writelines(merged_lines)
                print(f"[INFO]   Injected extra annotations into {block['name']}")
            else:
                fh.writelines(block["lines"])

            if block["kind"] == "class" and block["name"]:
                exported.append(block["name"])

    return exported


def write_init(
    path: Path,
    chunk_files: list[tuple[str, list[str]]],
    header_blocks: list[dict],
) -> None:
    """
    Write the __init__.pyi that:
      1. Re-emits the module-level header (imports, assignments)
      2. Imports and re-exports every name from every chunk file
    """
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# Auto-generated by split_bpy_types.py -- do not edit by hand.\n")
        fh.write("# Re-exports all bpy.types definitions from chunked sub-files.\n\n")

        # Re-emit header so module-level symbols (type aliases, etc.) are visible
        for block in header_blocks:
            fh.writelines(block["lines"])

        fh.write("\n\n")

        # Re-export from each chunk
        for module_name, names in chunk_files:
            if not names:
                continue
            names_str = ", ".join(f"{n} as {n}" for n in names)
            fh.write(f"from .{module_name} import {names_str}\n")

        fh.write("\n")

        # Build __all__ for explicit re-export (satisfies strict Pyright/mypy)
        all_names = [name for _, names in chunk_files for name in names]
        if all_names:
            fh.write("\n__all__ = [\n")
            for name in all_names:
                fh.write(f'    "{name}",\n')
            fh.write("]\n")


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------

def find_bpy_package_dir() -> Path:
    """
    Import bpy and return the Path to its package directory inside site-packages.
    Aborts with a clear message if bpy is not importable.
    """
    try:
        import bpy  # noqa: PLC0415
    except ImportError:
        print(
            "[ERROR] Could not import bpy. Run this script with the same Python "
            "interpreter that has fake-bpy-module installed.",
            file=sys.stderr,
        )
        sys.exit(1)

    bpy_path = getattr(bpy, "__path__", None)
    try:
        bpy_dir = Path(bpy_path[0])
    except (TypeError, IndexError):
        print(
            "[ERROR] Could not determine bpy package directory from bpy.__path__. "
            f"Got: {bpy_path!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[INFO] Detected bpy package at: {bpy_dir}")
    return bpy_dir


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------

def undo(bpy_dir: Path) -> None:
    """Reverse a previous run: restore types/__init__.pyi and delete the chunk files."""
    types_dir = bpy_dir / "types"
    hidden = types_dir / "_init.pyi"
    original = types_dir / "__init__.pyi"

    if not hidden.exists():
        print(
            f"[ERROR] {hidden} not found -- either this script was never run, "
            "or it was already undone.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Remove generated chunk files and the generated __init__.pyi
    for chunk_file in types_dir.glob(f"{CHUNK_PREFIX}*.pyi"):
        chunk_file.unlink()
        print(f"[INFO] Removed {chunk_file.name}")
    if original.exists():
        original.unlink()

    hidden.rename(original)
    print(f"[INFO] Restored {original}")
    print("[DONE] Undo complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Split fake-bpy-module's bpy/types/__init__.pyi in-place into a "
            "package of smaller files so PyCharm can index them."
        )
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Maximum number of class definitions per output file (default: {CHUNK_SIZE})",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Restore the original types/__init__.pyi and remove the generated chunk files.",
    )
    args = parser.parse_args()

    bpy_dir = find_bpy_package_dir()

    if args.undo:
        undo(bpy_dir)
        return

    # --- Load extra stubs (optional) -----------------------------------------

    extra_stubs_path = Path(__file__).parent / EXTRA_STUBS_FILENAME
    extra_stubs = load_extra_stubs(extra_stubs_path)
    if extra_stubs is None:
        print(f"[INFO] No extra stubs file found at {extra_stubs_path} -- skipping injection.")
    else:
        print(
            f"[INFO] Loaded extra stubs for {len(extra_stubs.classes)} class(es): "
            f"{', '.join(extra_stubs.classes)}"
        )

    # --- Locate types/__init__.pyi -------------------------------------------

    output_dir = bpy_dir / "types"
    input_path = output_dir / "__init__.pyi"
    hidden_path = output_dir / "_init.pyi"

    if not output_dir.is_dir():
        print(f"[ERROR] Expected a types/ package directory at {output_dir}", file=sys.stderr)
        sys.exit(1)

    if not input_path.exists():
        if hidden_path.exists():
            print(
                "[ERROR] types/__init__.pyi has already been renamed to _init.pyi -- "
                "looks like this script was already run. Use --undo first if "
                "you want to start over.",
                file=sys.stderr,
            )
        else:
            print(f"[ERROR] Could not find {input_path}", file=sys.stderr)
        sys.exit(1)

    # --- Read and parse ------------------------------------------------------

    print(f"[INFO] Reading {input_path} ({input_path.stat().st_size / 1024 / 1024:.1f} MB)")
    source = input_path.read_text(encoding="utf-8")

    print("[INFO] Parsing top-level blocks...")
    blocks = parse_top_level_blocks(source)

    class_count = sum(1 for b in blocks if b["kind"] == "class")
    print(f"[INFO] Found {len(blocks)} top-level blocks ({class_count} classes)")

    header_blocks, chunks = group_blocks_into_chunks(blocks, args.chunk_size)
    print(f"[INFO] Splitting into {len(chunks)} chunks of ~{args.chunk_size} classes each")

    # --- Write chunk files into the existing types/ dir ----------------------

    # Remove any previous chunk files from a prior run before writing new ones
    for old_chunk in output_dir.glob(f"{CHUNK_PREFIX}*.pyi"):
        old_chunk.unlink()

    chunk_files: list[tuple[str, list[str]]] = []
    pad = math.floor(math.log10(max(len(chunks), 1))) + 1

    for i, chunk_blocks in enumerate(chunks):
        module_name = f"{CHUNK_PREFIX}{str(i).zfill(pad)}"
        chunk_path = output_dir / f"{module_name}.pyi"
        exported = write_chunk(chunk_path, header_blocks, chunk_blocks, extra_stubs)
        chunk_files.append((module_name, exported))
        print(f"[INFO] Wrote {chunk_path.name} ({len(exported)} classes)")

    # --- Hide the original and write the new __init__.pyi --------------------

    input_path.rename(hidden_path)
    print(f"[INFO] Renamed __init__.pyi -> _init.pyi (hidden from PyCharm)")

    init_path = output_dir / "__init__.pyi"
    write_init(init_path, chunk_files, header_blocks)
    print(f"[INFO] Wrote {init_path}")

    total_exported = sum(len(names) for _, names in chunk_files)
    print(
        f"\n[DONE] {total_exported} classes exported across {len(chunks)} files.\n"
        f"       Invalidate PyCharm's caches (File -> Invalidate Caches) to pick up the changes.\n"
        f"       Run with --undo to restore the original state."
    )


if __name__ == "__main__":
    main()
