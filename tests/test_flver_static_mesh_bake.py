"""Headless check that FLVERs mixing static and dynamic meshes import to the right place in Blender.

Why a separate suite from ``test_flver_import_roundtrip.py``
-----------------------------------------------------------
The round-trip suite proves that Blender -> FLVER -> Blender is self-consistent and that counts are
preserved. It cannot catch a transform bug that is applied symmetrically on import and export, and
it never looks at where the mesh actually ends up. This suite instead compares the imported mesh
against an INDEPENDENT ground truth derived straight from the FLVER file.

The invariant
-------------
A FLVER mesh with ``is_dynamic = False`` stores its vertices in the local space of the single bone
each vertex is weighted to; a mesh with ``is_dynamic = True`` stores them in armature space. A few
Demon's Souls characters mix both kinds in one model (eyes, cloaks, and alternate weapons are
static while the body is dynamic), which one Blender Armature cannot represent directly: Blender
rest bones can only match one convention.

The add-on resolves this by keeping the whole Blender mesh in armature space -- baking the static
meshes' vertices through their bone's armature-space rest transform on import, and reversing that
on export. Two things must therefore hold after import:

  * every Blender vertex sits at its FLVER vertex's armature-space position, and
  * the Armature modifier is the identity at rest, i.e. evaluating the mesh through it does not
    move a single vertex.

Before this was handled, these models fell back to ``CUSTOM`` bone data (FLVER transforms written
to PoseBones, EditBones left as origin stubs), which posed the armature-space dynamic meshes by
their bones' full armature transforms a second time and tore the model apart -- DeS c2030 was
displaced by up to 1.75 units. Deleting the Armature made the mesh look correct again, which is the
signature of this bug.

The export half is checked too: the static meshes must come back out as static, with their vertices
returned to bone-local space and their bone weights zeroed, exactly as vanilla stores them.

Run with:
    blender --background --python tests/test_flver_static_mesh_bake.py
"""
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import bpy
import numpy as np
import bl_test_utils as T

T.enable_addon()

from soulstruct.config import Config
from soulstruct.flver import FLVER
from soulstruct.flver.bone_tools import BoneTree

# Blender vertices are float32, and the bake is float32 maths, so anything below this is noise.
MAX_POSITION_DIFF = 1e-4
# Rows per chunk when brute-forcing nearest-neighbour distances (keeps the distance matrix small).
POSITION_CHUNK_SIZE = 256


@dataclass
class StaticBakeCase(T.ImportCaseBase):
    """One FLVER that mixes `is_dynamic` meshes."""

    # Expected number of static (non-dynamic) FLVER meshes in the source file (sanity check that the
    # test case is still exercising what it claims to).
    expect_static_meshes: int = 0


STATIC_BAKE_TEST_CASES: list[StaticBakeCase] = [
    # Every known Demon's Souls character whose FLVER mixes static and dynamic meshes.
    StaticBakeCase(
        name="DES / c2030 (Fat Official) / cloak",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c2030",
        filename="c2030.flver",
        expect_static_meshes=1,
    ),
    StaticBakeCase(
        name="DES / c2100 (Vanguard) / eye + alternate weapons",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c2100",
        filename="c2100.flver",
        expect_static_meshes=3,
    ),
    StaticBakeCase(
        name="DES / c2101 (Vanguard variant) / alternate weapons",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c2101",
        filename="c2101.flver",
        expect_static_meshes=2,
    ),
    StaticBakeCase(
        name="DES / c3060 (Gargoyle) / eyes",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c3060",
        filename="c3060.flver",
        expect_static_meshes=1,
    ),
    StaticBakeCase(
        name="DES / c3140 (Giant Depraved One) / mouth",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c3140",
        filename="c3140.flver",
        expect_static_meshes=1,
    ),
    StaticBakeCase(
        name="DES / c7090 (Maiden in Black) / cloth",
        game_enum="DEMONS_SOULS",
        directory=Config.DES_PATH / "chr/c7090",
        filename="c7090.flver",
        expect_static_meshes=1,
    ),
]


def get_armature_space_positions(flver: FLVER) -> np.ndarray:
    """Independent ground truth: every FLVER vertex position in armature space, in Blender coordinates.

    Deliberately does NOT use any add-on code. Dynamic mesh vertices are already in armature space;
    static mesh vertices are transformed by the armature-space rest transform of their single bone.
    """
    bone_arma_transforms = BoneTree(flver).get_bone_armature_space_transforms()
    all_positions = []
    for mesh in flver.meshes:
        array = mesh.vertex_arrays[0].array
        positions = np.array(array["position"])[:, :3].astype(np.float64)
        if mesh.is_dynamic:
            all_positions.append(positions)
            continue
        # First vertex bone index is local to `mesh.bone_indices` (all four are the same for static meshes).
        local_bone_indices = np.array(array["bone_indices"])[:, 0]
        global_bone_indices = np.array(mesh.bone_indices)[local_bone_indices]
        arma_positions = np.empty_like(positions)
        for bone_index in np.unique(global_bone_indices):
            bone_mask = global_bone_indices == bone_index
            translate, rotate, scale = bone_arma_transforms[int(bone_index)]
            arma_positions[bone_mask] = (
                (np.array(list(scale)) * positions[bone_mask]) @ np.array(rotate.data).T + np.array(list(translate))
            )
        all_positions.append(arma_positions)
    game_positions = np.concatenate(all_positions, axis=0)
    return game_positions[:, [0, 2, 1]]  # FromSoft -> Blender (swap Y and Z)


def get_vertex_positions(mesh_obj: bpy.types.Object) -> np.ndarray:
    positions = np.empty(len(mesh_obj.data.vertices) * 3, dtype=np.float32)
    mesh_obj.data.vertices.foreach_get("co", positions)
    return positions.reshape(-1, 3)


def get_evaluated_vertex_positions(mesh_obj: bpy.types.Object) -> np.ndarray:
    """Vertex positions after modifiers (i.e. after the Armature modifier deforms the rest pose)."""
    evaluated_obj = mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    evaluated_mesh = evaluated_obj.to_mesh()
    try:
        positions = np.empty(len(evaluated_mesh.vertices) * 3, dtype=np.float32)
        evaluated_mesh.vertices.foreach_get("co", positions)
        return positions.reshape(-1, 3)
    finally:
        evaluated_obj.to_mesh_clear()


def get_max_position_error(positions: np.ndarray, expected_positions: np.ndarray) -> float:
    """Largest distance from any row of `positions` to its nearest row in `expected_positions`.

    Vertex counts and order differ between the two (Blender merges vertices and drops degenerate
    faces), so we can only check that every vertex landed on SOME expected position.
    """
    positions = positions.astype(np.float64)
    expected_positions = expected_positions.astype(np.float64)
    worst = 0.0
    for start in range(0, len(positions), POSITION_CHUNK_SIZE):
        chunk = positions[start:start + POSITION_CHUNK_SIZE]
        distances = np.linalg.norm(chunk[:, None, :] - expected_positions[None, :, :], axis=2)
        worst = max(worst, float(distances.min(axis=1).max()))
    return worst


def run_case(case: StaticBakeCase):
    T.clear_scene()
    T.set_game(case.game_enum)

    flver = FLVER.from_path(Path(case.directory) / case.filename)
    static_mesh_count = sum(1 for mesh in flver.meshes if not mesh.is_dynamic)
    if static_mesh_count != case.expect_static_meshes:
        T.fail(
            case.name,
            f"Source FLVER has {static_mesh_count} static meshes, expected {case.expect_static_meshes}. "
            f"This test case no longer exercises mixed static/dynamic meshes.",
        )
        return
    if all(not mesh.is_dynamic for mesh in flver.meshes):
        T.fail(case.name, "Source FLVER has no dynamic meshes; not a mixed FLVER.")
        return

    expected_positions = get_armature_space_positions(flver)

    result = T.call_op(
        "import_scene.flver", directory=str(case.directory), files=[{"name": case.filename}]
    )
    if "FINISHED" not in result:
        T.fail(case.name, f"Import operator returned {result}")
        return

    flver_objs = T.find_objects_by_soulstruct_type("FLVER")
    if len(flver_objs) != 1:
        T.fail(case.name, f"Expected exactly one imported FLVER object, got {len(flver_objs)}")
        return
    mesh_obj = flver_objs[0]

    # 1. Mixed FLVERs must use EDIT bone data (armature-space rest bones), not CUSTOM.
    if mesh_obj.FLVER.bone_data_type != "EditBone":
        T.fail(
            case.name,
            f"Expected 'EditBone' bone data for a FLVER with dynamic meshes, got "
            f"'{mesh_obj.FLVER.bone_data_type}'. Dynamic mesh vertices are in armature space and will be "
            f"posed a second time by the Armature otherwise.",
        )
        return

    # 2. Every Blender vertex must sit at its FLVER vertex's armature-space position.
    positions = get_vertex_positions(mesh_obj)
    position_error = get_max_position_error(positions, expected_positions)
    if position_error > MAX_POSITION_DIFF:
        T.fail(
            case.name,
            f"A Blender vertex is {position_error:.4g} away from any FLVER vertex's armature-space position "
            f"(tolerance {MAX_POSITION_DIFF:g}); static mesh vertices were not baked out of bone-local space "
            f"correctly.",
        )
        return

    # 3. The Armature modifier must not move anything at rest.
    rest_deviation = float(np.abs(get_evaluated_vertex_positions(mesh_obj) - positions).max())
    if rest_deviation > MAX_POSITION_DIFF:
        T.fail(
            case.name,
            f"Armature modifier deforms the mesh at rest by up to {rest_deviation:.4g} "
            f"(tolerance {MAX_POSITION_DIFF:g}). The rest pose does not match the mesh's bind pose.",
        )
        return

    # 4. Export must restore the vanilla static mesh structure.
    with tempfile.TemporaryDirectory() as tmp_dir:
        export_path = str(Path(tmp_dir) / case.filename)
        T.activate(mesh_obj)
        result = T.call_op("export_scene.flver", filepath=export_path, dcx_type="Null")
        if "FINISHED" not in result:
            T.fail(case.name, f"Export operator returned {result}")
            return
        exported_flver = FLVER.from_path(export_path)

    exported_static_meshes = [mesh for mesh in exported_flver.meshes if not mesh.is_dynamic]
    if len(exported_static_meshes) != static_mesh_count:
        T.fail(
            case.name,
            f"Exported FLVER has {len(exported_static_meshes)} static meshes, expected {static_mesh_count}.",
        )
        return

    for mesh in exported_static_meshes:
        array = mesh.vertex_arrays[0].array
        if "bone_weights" in array.dtype.names and np.any(np.array(array["bone_weights"]) != 0.0):
            T.fail(case.name, "Exported static mesh has non-zero bone weights (vanilla static meshes have none).")
            return
        bone_indices = np.array(array["bone_indices"])
        if not np.all(bone_indices == bone_indices[:, :1]):
            T.fail(case.name, "Exported static mesh vertex uses more than one bone index.")
            return

    # Re-exported vertices, transformed back into armature space, must match the original file.
    export_error = get_max_position_error(get_armature_space_positions(exported_flver), expected_positions)
    if export_error > MAX_POSITION_DIFF:
        T.fail(
            case.name,
            f"A re-exported vertex is {export_error:.4g} away from any original armature-space position "
            f"(tolerance {MAX_POSITION_DIFF:g}); static mesh vertices were not returned to bone-local space "
            f"correctly.",
        )
        return

    T.ok(
        case.name,
        f"{len(positions)} vertices in armature space, identity rest pose, "
        f"{static_mesh_count} static mesh(es) round-tripped",
    )


def main():
    import argparse
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter-test-names", type=str, default="")
    args = parser.parse_args(argv)
    T.run_case_list(
        STATIC_BAKE_TEST_CASES,
        run_case,
        suite_name="FLVER static mesh bake",
        filter_test_names=args.filter_test_names,
    )


main()
