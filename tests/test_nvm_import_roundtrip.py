"""Headless NVM navmesh import/export round-trip tests.

NVM is the navmesh format used in Demon's Souls and Dark Souls 1 (PTDE / DSR).

Round-trip methodology per case
---------------------------------
1. Import a loose ``n*.nvm`` file with ``import_scene.nvm``.
2. Validate: at least one NAVMESH-typed Mesh was created.
3. Export with ``export_scene.nvm`` to a temp file.
4. Verify the exported file is parseable (``NVM.from_path``).
5. Re-import the exported file; compare polygon count.
6. Re-export to a second temp file; compare Soulstruct triangle counts.
7. Clean up.

FILE PATHS
----------
Fill in ``directory`` / ``filename`` for the games you have installed.
Leave both as empty strings to auto-skip.

Run with:
    blender --background --python tests/test_nvm_import_roundtrip.py
"""
import sys
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import bl_test_utils as T
from soulstruct.base.maps.navmesh.nvm import NVM

T.enable_addon()

# ---------------------------------------------------------------------------
# Game path constants
# ---------------------------------------------------------------------------

from soulstruct.config import Config

# ---------------------------------------------------------------------------
# Test case descriptor
# ---------------------------------------------------------------------------

@dataclass
class NVMImportCase(T.ImportCaseBase):
    """One NVM navmesh import/export round-trip test.

    ``filename`` should be a loose ``n*.nvm`` file.
    """

    # Expected triangle count (None = skip check).
    expect_triangle_count: int | None = None


# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------

NVM_TEST_CASES: list[NVMImportCase] = [

    # ------------------------------------------------------------------
    # Demon's Souls  (optional)
    # ------------------------------------------------------------------
    NVMImportCase(
        name="DES / Map m02 / navmesh",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "map/m02_00_00_00",  # Boletaria Palace
        filename="n0003b0.nvm",
        tags=["navmesh"],
    ),
    NVMImportCase(
        name="DES / Map m01 / navmesh",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "map/m01_00_00_00",  # Nexus
        filename="n0000b0.nvm",
        tags=["navmesh"],
    ),
    NVMImportCase(
        name="DES / Map m07 / navmesh",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "map/m07_01_00_00",  # Northern Limits (unused)
        filename="n0000b1.nvm",
        tags=["navmesh"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls PTDE
    # ------------------------------------------------------------------
    NVMImportCase(
        name="PTDE / Map m10 / n0010B0A10",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/m10_02_00_00",
        filename="n0010B0A10.nvm",
        tags=["navmesh"],
    ),
    NVMImportCase(
        name="PTDE / Map m12 / navmesh",
        game_enum="DARK_SOULS_PTDE",
        directory=Config.PTDE_PATH / "map/m12_00_00_00",
        filename="n0100B0A12.nvm",
        tags=["navmesh"],
    ),

    # ------------------------------------------------------------------
    # Dark Souls Remastered
    # ------------------------------------------------------------------
    NVMImportCase(
        name="DSR / Map m10 / n0010B0A10",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/m10_02_00_00",
        filename="m10_02_00_00.nvmbnd.dcx",
        tags=["navmesh"],
    ),
    NVMImportCase(
        name="DSR / Map m10 / n0020B0A10",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/m10_02_00_00",
        filename="m10_02_00_00.nvmbnd.dcx",
        tags=["navmesh"],
    ),
    NVMImportCase(
        name="DSR / Map m12 / n0007B0A12",
        game_enum="DARK_SOULS_DSR",
        directory=Config.DSR_PATH / "map/m12_00_00_01",
        filename="m12_00_00_01.nvmbnd.dcx",
        tags=["navmesh"],
    ),
]


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _navmesh_scene_stats() -> dict:
    """Collect coarse statistics about all NAVMESH objects in the scene."""
    objs = T.find_objects_by_soulstruct_type("NAVMESH")
    poly_count = sum(len(o.data.polygons) for o in objs)
    vert_count = sum(len(o.data.vertices) for o in objs)
    return {"obj_count": len(objs), "poly_count": poly_count, "vert_count": vert_count}


# ---------------------------------------------------------------------------
# Binder detection
# ---------------------------------------------------------------------------

_NVMBND_RE = re.compile(r"\.nvmbnd(\.dcx)?$", re.IGNORECASE)


def _is_nvmbnd(filename: str) -> bool:
    """Return True if *filename* is an NVMBND binder (with or without DCX)."""
    return bool(_NVMBND_RE.search(filename))


# ---------------------------------------------------------------------------
# Per-case test runner
# ---------------------------------------------------------------------------

def run_case(case: NVMImportCase):
    """Full round-trip for one or all NVM entries.

    When the source file is an ``nvmbnd(.dcx)`` binder the operator is called
    with ``import_all_from_binder=True`` and every resulting NAVMESH object is
    individually exported, re-imported, and re-exported.  For a loose ``.nvm``
    file the same pipeline runs on the single object.
    """

    # ---- 1. Import ----
    T.clear_scene()
    T.set_game(case.game_enum)

    is_binder = _is_nvmbnd(case.operator_filename)

    try:
        import_kwargs: dict = dict(
            directory=str(case.directory),
            files=[{"name": case.operator_filename}],
        )
        if is_binder:
            import_kwargs["import_all_from_binder"] = True
        result = bpy.ops.import_scene.nvm("EXEC_DEFAULT", **import_kwargs)
    except Exception as ex:
        T.fail(case.name, f"Import raised exception: {ex}")
        return
    if "FINISHED" not in result:
        T.fail(case.name, f"Import returned {result}")
        return

    # ---- 2. Validate ----
    nvm_objs = T.find_objects_by_soulstruct_type("NAVMESH")
    if not nvm_objs:
        T.fail(case.name, "No NAVMESH objects found after import")
        return

    if case.expect_triangle_count is not None:
        actual = sum(len(o.data.polygons) for o in nvm_objs)
        if actual != case.expect_triangle_count:
            T.fail(case.name, f"Expected {case.expect_triangle_count} triangles, got {actual}")
            return

    stats_1 = _navmesh_scene_stats()

    # Will be set inside the tmpdir block; needed for the final ok() message.
    total_tris_1: int = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # ---- 3. Export every NAVMESH object to a separate .nvm file ----
        for nvm_obj in nvm_objs:
            model_stem = nvm_obj.name.split(".")[0].split(" ")[0]
            T.activate(nvm_obj)
            export_path = str(tmpdir_path / f"{model_stem}.nvm")
            try:
                export_result = bpy.ops.export_scene.nvm(
                    "EXEC_DEFAULT",
                    filepath=export_path,
                    dcx_type="Null",
                )
            except Exception as ex:
                T.fail(case.name, f"Export of '{model_stem}' raised exception: {ex}")
                return
            if "FINISHED" not in export_result:
                T.fail(case.name, f"Export of '{model_stem}' returned {export_result}")
                return

        exported_1 = sorted(tmpdir_path.glob("*.nvm"))
        if not exported_1:
            T.fail(case.name, "No .nvm files found in temp dir after export")
            return
        if len(exported_1) != len(nvm_objs):
            T.fail(
                case.name,
                f"Expected {len(nvm_objs)} exported .nvm file(s), found {len(exported_1)}",
            )
            return

        # ---- 4. Verify every exported file is parseable ----
        nvm_parsed_1: list[NVM] = []
        for f in exported_1:
            try:
                nvm_parsed_1.append(NVM.from_path(f))
            except Exception as ex:
                T.fail(case.name, f"Exported '{f.name}' not parseable: {ex}")
                return

        total_tris_1 = sum(len(n.triangles) for n in nvm_parsed_1)
        if total_tris_1 == 0 and stats_1["poly_count"] > 0:
            T.fail(case.name, "Exported NVMs have no triangles but source had polygons")
            return

        # ---- 5. Re-import every exported file ----
        T.clear_scene()
        T.set_game(case.game_enum)
        for f in exported_1:
            try:
                r2 = bpy.ops.import_scene.nvm(
                    "EXEC_DEFAULT",
                    directory=str(tmpdir_path),
                    files=[{"name": f.name}],
                )
            except Exception as ex:
                T.fail(case.name, f"Re-import of '{f.name}' raised exception: {ex}")
                return
            if "FINISHED" not in r2:
                T.fail(case.name, f"Re-import of '{f.name}' returned {r2}")
                return

        nvm_objs_2 = T.find_objects_by_soulstruct_type("NAVMESH")
        if not nvm_objs_2:
            T.fail(case.name, "No NAVMESH objects found after re-import")
            return

        # ---- 6. Compare Blender statistics ----
        stats_2 = _navmesh_scene_stats()
        if stats_1["obj_count"] != stats_2["obj_count"]:
            T.fail(
                case.name,
                f"Object count differs after re-import: "
                f"{stats_1['obj_count']} → {stats_2['obj_count']}",
            )
            return
        if stats_1["poly_count"] != stats_2["poly_count"]:
            T.fail(
                case.name,
                f"Poly count differs after re-import: "
                f"{stats_1['poly_count']} → {stats_2['poly_count']}",
            )
            return

        # ---- 7. Second export of every re-imported object ----
        for nvm_obj_2 in nvm_objs_2:
            model_stem_2 = nvm_obj_2.name.split(".")[0].split(" ")[0]
            T.activate(nvm_obj_2)
            export_path_2 = str(tmpdir_path / f"{model_stem_2}_2.nvm")
            try:
                export_result_2 = bpy.ops.export_scene.nvm(
                    "EXEC_DEFAULT",
                    filepath=export_path_2,
                    dcx_type="Null",
                )
            except Exception as ex:
                T.fail(case.name, f"Second export of '{model_stem_2}' raised exception: {ex}")
                return
            if "FINISHED" not in export_result_2:
                T.fail(case.name, f"Second export of '{model_stem_2}' returned {export_result_2}")
                return

        exported_2 = sorted(p for p in tmpdir_path.glob("*_2.nvm"))
        if not exported_2:
            T.fail(case.name, "No *_2.nvm files found after second export")
            return

        # ---- 8. Parse second exports; compare total triangle counts ----
        nvm_parsed_2: list[NVM] = []
        for f in exported_2:
            try:
                nvm_parsed_2.append(NVM.from_path(f))
            except Exception as ex:
                T.fail(case.name, f"Second exported '{f.name}' not parseable: {ex}")
                return

        total_tris_2 = sum(len(n.triangles) for n in nvm_parsed_2)
        if total_tris_1 != total_tris_2:
            T.fail(
                case.name,
                f"Total triangle count differs between exports: "
                f"{total_tris_1} vs {total_tris_2}",
            )
            return

        # ---- 9. Exact equality check on the first NVM of this test case ----
        # Compare nvm_parsed_1[0] (exported from game import) with nvm_parsed_2[0]
        # (exported from re-import of that first export), field by field.
        if nvm_parsed_1 and nvm_parsed_2:
            nvm_a = nvm_parsed_1[0]
            nvm_b = nvm_parsed_2[0]

            # Vertices (numpy array).
            if not np.array_equal(nvm_a.vertices, nvm_b.vertices):
                T.fail(
                    case.name,
                    f"First NVM vertices differ — "
                    f"shapes {nvm_a.vertices.shape} vs {nvm_b.vertices.shape}, "
                    f"max abs diff {np.max(np.abs(nvm_a.vertices - nvm_b.vertices)):.6f}",
                )
                return

            # Triangles (list of NVMTriangle dataclasses).
            if len(nvm_a.triangles) != len(nvm_b.triangles):
                T.fail(
                    case.name,
                    f"First NVM triangle count differs: "
                    f"{len(nvm_a.triangles)} vs {len(nvm_b.triangles)}",
                )
                return
            for i, (ta, tb) in enumerate(zip(nvm_a.triangles, nvm_b.triangles)):
                if ta != tb:
                    T.fail(case.name, f"First NVM triangle[{i}] differs: {ta!r} vs {tb!r}")
                    return

            # Quadtree boxes — compare all leaf nodes' triangle-index lists.
            leaves_a = [box for box, _ in NVM.get_all_boxes(nvm_a.root_box) if box.is_leaf]
            leaves_b = [box for box, _ in NVM.get_all_boxes(nvm_b.root_box) if box.is_leaf]
            if len(leaves_a) != len(leaves_b):
                T.fail(
                    case.name,
                    f"First NVM leaf-box count differs: {len(leaves_a)} vs {len(leaves_b)}",
                )
                return
            for i, (ba, bb) in enumerate(zip(leaves_a, leaves_b)):
                if ba.triangle_indices != bb.triangle_indices:
                    T.fail(
                        case.name,
                        f"First NVM leaf-box[{i}] triangle indices differ: "
                        f"{ba.triangle_indices} vs {bb.triangle_indices}",
                    )
                    return

            # Event entities (list of NVMEventEntity dataclasses).
            if len(nvm_a.event_entities) != len(nvm_b.event_entities):
                T.fail(
                    case.name,
                    f"First NVM event-entity count differs: "
                    f"{len(nvm_a.event_entities)} vs {len(nvm_b.event_entities)}",
                )
                return
            for i, (ea, eb) in enumerate(zip(nvm_a.event_entities, nvm_b.event_entities)):
                if ea != eb:
                    T.fail(
                        case.name,
                        f"First NVM event_entity[{i}] differs: "
                        f"id {ea.entity_id} vs {eb.entity_id}, "
                        f"triangles {ea.triangle_indices} vs {eb.triangle_indices}",
                    )
                    return

    T.ok(
        case.name,
        f"NVM round-trip OK — {stats_1['obj_count']} obj(s), "
        f"{stats_1['poly_count']} poly(s), {total_tris_1} tri(s) total",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    T.run_case_list(NVM_TEST_CASES, run_case, suite_name="NVM navmesh import/export")


main()
