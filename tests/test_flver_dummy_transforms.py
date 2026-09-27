"""Tests for FLVER Dummy transform conversion (no game files required).

These tests check that an imported Dummy actually LANDS where the FLVER says it should, in Blender world space --
not merely that import/export round-trip each other. A symmetric error in both directions (e.g. using the wrong
attach-bone parent space on both sides) round-trips perfectly while leaving every Dummy visibly misplaced in
Blender, so round-trip equality alone is not enough.

Covers:
  - `BlenderFLVERDummy.new_from_soulstruct_obj`  (import)
  - `BlenderFLVERDummy.to_soulstruct_obj`        (export)
  - Blender bone-parenting space (`parent_type='BONE'`, which is rooted at the bone TAIL and keeps the FLVER
    X-forward bone change-of-basis)

Run with:
    blender --background --python tests/test_flver_dummy_transforms.py
"""
import sys
from pathlib import Path

# Ensure this tests/ directory is on the path so bl_test_utils is importable.
sys.path.insert(0, str(Path(__file__).parent))

import bpy
from mathutils import Matrix

import bl_test_utils as T

T.enable_addon()
T.set_game("DARK_SOULS_DSR")

from bl_ext.user_default.io_soulstruct.soulstruct.blender.flver.models.types import BlenderFLVERDummy, FLVERBoneDataType
from bl_ext.user_default.io_soulstruct.soulstruct.blender.flver.utilities import (
    BONE_CoB_4x4,
    game_bone_transform_to_bl_bone_matrix,
    game_forward_up_vectors_to_bl_euler,
)
from bl_ext.user_default.io_soulstruct.soulstruct.blender.utilities.conversion import to_blender

from soulstruct.flver import Dummy
from soulstruct.utilities.maths import Matrix3, Vector3

DUMMY_TESTS = []

TOL = 1e-5

# Two arbitrary, deliberately non-trivial game armature-space bone transforms (translate, rotation, scale) and the
# Blender bone lengths to give them. Non-identity rotations and distinct non-default lengths are what expose an
# incorrect bone-parent space.
BONE_DEFS = [
    ("Master", Vector3((0.0, 0.0, 0.0)), (0.0, 0.0, 0.0), 0.37),
    ("R_Hand", Vector3((0.3, 1.4, -0.2)), (0.4, -0.9, 0.25), 0.21),
    ("Sfx", Vector3((-0.1, 0.8, 0.6)), (-0.7, 0.15, 1.1), 0.13),
]


def _make_test_armature() -> bpy.types.Object:
    """Build an Armature whose bones are placed exactly as FLVER import places them (game transform + X-forward CoB),
    with distinct non-zero lengths."""
    armature_data = bpy.data.armatures.new("TestFLVER Armature")
    armature = bpy.data.objects.new("TestFLVER Armature", armature_data)
    bpy.context.scene.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    for name, translate, rotate_rad, length in BONE_DEFS:
        edit_bone = armature_data.edit_bones.new(name)
        edit_bone.head = (0.0, 0.0, 0.0)
        edit_bone.tail = (0.0, 0.1, 0.0)  # non-zero length required before assigning `matrix`
        rotmat = Matrix3.from_euler_angles_rad(rotate_rad)
        edit_bone.matrix = game_bone_transform_to_bl_bone_matrix(translate, rotmat, Vector3((1.0, 1.0, 1.0)))
        edit_bone.length = length
    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def _game_bone_matrix(armature: bpy.types.Object, bone_index: int) -> Matrix:
    """The bone's armature-space transform in pure `to_blender()` space, i.e. with the X-forward CoB undone.

    This is the space FLVER Dummy transforms are stored in, and is computed here independently of the Dummy code
    under test.
    """
    return armature.data.bones[bone_index].matrix_local @ BONE_CoB_4x4


def _expected_dummy_world(armature: bpy.types.Object, dummy: Dummy) -> Matrix:
    """Where the Dummy must end up in Blender world space (Armature is at the origin, so world == armature space).

    Derived straight from the FLVER definition: the Dummy transform is in the space of its `parent_bone` (or model
    space if it has none). The `attach_bone` is irrelevant to WHERE the Dummy sits at rest -- it only determines
    what the Dummy follows during animation -- so it does not appear here at all.
    """
    upward = dummy.upward if dummy.use_upward_vector else Vector3((0.0, 1.0, 0.0))
    bl_euler = game_forward_up_vectors_to_bl_euler(Vector3(dummy.forward), Vector3(upward))
    local = Matrix.LocRotScale(to_blender(Vector3(dummy.translate)), bl_euler, (1.0, 1.0, 1.0))
    if dummy.parent_bone_index != -1:
        return _game_bone_matrix(armature, dummy.parent_bone_index) @ local
    return local


def _matrices_close(a: Matrix, b: Matrix, tol: float = TOL) -> bool:
    return all(abs(x - y) <= tol for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b))


def _max_matrix_diff(a: Matrix, b: Matrix) -> float:
    return max(abs(x - y) for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b))


def _import_dummy(armature: bpy.types.Object, dummy: Dummy) -> BlenderFLVERDummy:
    return BlenderFLVERDummy.new_from_soulstruct_obj(
        operator=None,
        context=bpy.context,
        soulstruct_obj=dummy,
        name=f"TestFLVER Dummy<0> [{dummy.reference_id}]",
        armature=armature,
        collection=bpy.context.scene.collection,
    )


def _check_placement(test_name: str, dummy: Dummy):
    """Import `dummy` and assert it lands at its FLVER-defined world transform."""
    T.clear_scene()
    armature = _make_test_armature()
    bl_dummy = _import_dummy(armature, dummy)
    bpy.context.view_layer.update()

    expected = _expected_dummy_world(armature, dummy)
    actual = bl_dummy.obj.matrix_world
    T.assert_true(
        _matrices_close(actual, expected),
        f"{test_name}/world_transform",
        f"max component error {_max_matrix_diff(actual, expected):.6f} "
        f"(expected translation {tuple(round(v, 4) for v in expected.translation)}, "
        f"got {tuple(round(v, 4) for v in actual.translation)})",
    )


def _check_roundtrip(test_name: str, dummy: Dummy):
    """Import `dummy`, export it again, and assert every transform field survives."""
    T.clear_scene()
    armature = _make_test_armature()
    bl_dummy = _import_dummy(armature, dummy)
    bpy.context.view_layer.update()

    exported = bl_dummy.to_soulstruct_obj(operator=None, context=bpy.context, armature=armature)

    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(exported.translate, dummy.translate)),
        f"{test_name}/translate", f"expected {tuple(dummy.translate)}, got {tuple(exported.translate)}",
    )
    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(exported.forward, dummy.forward)),
        f"{test_name}/forward", f"expected {tuple(dummy.forward)}, got {tuple(exported.forward)}",
    )
    expected_upward = tuple(dummy.upward) if dummy.use_upward_vector else (0.0, 0.0, 0.0)
    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(exported.upward, expected_upward)),
        f"{test_name}/upward", f"expected {expected_upward}, got {tuple(exported.upward)}",
    )
    T.assert_equal(exported.parent_bone_index, dummy.parent_bone_index, f"{test_name}/parent_bone_index")
    T.assert_equal(exported.attach_bone_index, dummy.attach_bone_index, f"{test_name}/attach_bone_index")
    T.assert_equal(exported.reference_id, dummy.reference_id, f"{test_name}/reference_id")


# A Dummy with a non-axis-aligned orientation, used by most cases below. `forward` and `upward` are orthonormal.
_ANGLED_FORWARD = Vector3((0.6, 0.0, 0.8))
_ANGLED_UPWARD = Vector3((0.0, 1.0, 0.0))


def _dummy(parent_bone_index: int, attach_bone_index: int, reference_id: int = 200) -> Dummy:
    return Dummy(
        translate=Vector3((0.05, 0.12, -0.3)),
        forward=_ANGLED_FORWARD,
        upward=_ANGLED_UPWARD,
        reference_id=reference_id,
        parent_bone_index=parent_bone_index,
        attach_bone_index=attach_bone_index,
        use_upward_vector=True,
    )


# ---------------------------------------------------------------------------
# Placement (the actual bug: Dummies must align with the model, not just round-trip)
# ---------------------------------------------------------------------------

@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_attach_and_parent_bone():
    """Typical character Dummy: 'in space of' a categorical bone, attached to an animated bone."""
    _check_placement("test_dummy_placement_attach_and_parent_bone", _dummy(parent_bone_index=2, attach_bone_index=1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_same_attach_and_parent_bone():
    _check_placement(
        "test_dummy_placement_same_attach_and_parent_bone", _dummy(parent_bone_index=1, attach_bone_index=1)
    )


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_attach_bone_only():
    """No 'in space of' bone: FLVER transform is in model space, but the Dummy still follows an attach bone."""
    _check_placement("test_dummy_placement_attach_bone_only", _dummy(parent_bone_index=-1, attach_bone_index=1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_parent_bone_only():
    _check_placement("test_dummy_placement_parent_bone_only", _dummy(parent_bone_index=2, attach_bone_index=-1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_no_bones():
    _check_placement("test_dummy_placement_no_bones", _dummy(parent_bone_index=-1, attach_bone_index=-1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_root_bone_at_origin():
    """Attach bone 0 sits at the origin with identity rotation, so ONLY the tail offset can misplace this Dummy."""
    _check_placement("test_dummy_placement_root_bone_at_origin", _dummy(parent_bone_index=-1, attach_bone_index=0))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_forward_axis_points_along_game_forward():
    """The Dummy's Blender local +Y axis must point along its (converted) game `forward` vector."""
    T.clear_scene()
    armature = _make_test_armature()
    dummy = _dummy(parent_bone_index=-1, attach_bone_index=1)
    bl_dummy = _import_dummy(armature, dummy)
    bpy.context.view_layer.update()

    expected_forward = to_blender(Vector3(dummy.forward))
    actual_forward = bl_dummy.obj.matrix_world.to_3x3().col[1]
    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(actual_forward, expected_forward)),
        "test_dummy_forward_axis_points_along_game_forward",
        f"expected {tuple(round(v, 4) for v in expected_forward)}, got {tuple(round(v, 4) for v in actual_forward)}",
    )


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

@T.register_bl_test(DUMMY_TESTS)
def test_dummy_roundtrip_attach_and_parent_bone():
    _check_roundtrip("test_dummy_roundtrip_attach_and_parent_bone", _dummy(parent_bone_index=2, attach_bone_index=1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_roundtrip_attach_bone_only():
    """Also a regression test for the `parent_bone` getter raising `KeyError` when no parent bone is stored."""
    _check_roundtrip("test_dummy_roundtrip_attach_bone_only", _dummy(parent_bone_index=-1, attach_bone_index=1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_roundtrip_no_bones():
    _check_roundtrip("test_dummy_roundtrip_no_bones", _dummy(parent_bone_index=-1, attach_bone_index=-1))


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_roundtrip_no_upward_vector():
    dummy = _dummy(parent_bone_index=2, attach_bone_index=1)
    dummy.use_upward_vector = False
    _check_roundtrip("test_dummy_roundtrip_no_upward_vector", dummy)


# ---------------------------------------------------------------------------
# Bone-parent space helper
# ---------------------------------------------------------------------------

@T.register_bl_test(DUMMY_TESTS)
def test_bone_object_parent_matrix_matches_blender():
    """`get_bone_object_parent_matrix()` must equal the parent space Blender itself uses for bone-parented Objects."""
    from bl_ext.user_default.io_soulstruct.soulstruct.blender.flver.utilities import get_bone_object_parent_matrix

    T.clear_scene()
    armature = _make_test_armature()
    bone = armature.data.bones["R_Hand"]

    empty = bpy.data.objects.new("Probe", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = armature
    empty.parent_bone = bone.name
    empty.parent_type = "BONE"
    # An identity `matrix_local` means the Object sits exactly at Blender's parent matrix.
    empty.matrix_local = Matrix.Identity(4)
    bpy.context.view_layer.update()

    expected = get_bone_object_parent_matrix(bone)
    T.assert_true(
        _matrices_close(empty.matrix_world, expected),
        "test_bone_object_parent_matrix_matches_blender",
        f"max component error {_max_matrix_diff(empty.matrix_world, expected):.6f}",
    )


# ---------------------------------------------------------------------------
# Parent bone scale (e.g. DeS c5010/c1030 'sfx_dummy' bone, scale 3.5/2.9, used by all [200] Dummies)
# ---------------------------------------------------------------------------

def _game_arma_transforms(bone_defs, parents: dict[str, str]) -> dict[str, tuple[Vector3, Matrix3]]:
    """Independent FLVER armature-space (translate, rotmat) for LOCAL `bone_defs`, composed down `parents`."""
    result = {}
    for name, translate, rotate_rad, _length in bone_defs:
        rotmat = Matrix3.from_euler_angles_rad(rotate_rad)
        if name in parents:
            parent_t, parent_r = result[parents[name]]
            result[name] = (parent_t + parent_r @ translate, parent_r @ rotmat)
        else:
            result[name] = (translate, rotmat)
    return result


def _expected_world_from_game(
    arma: dict[str, tuple[Vector3, Matrix3]], bone_names: list[str], dummy: Dummy, parent_scale=(1.0, 1.0, 1.0)
) -> Matrix:
    """Expected Dummy world transform computed purely in game space, then converted: the game applies the parent
    bone's (local) scale to the Dummy's local translation."""
    upward = dummy.upward if dummy.use_upward_vector else Vector3((0.0, 1.0, 0.0))
    bl_euler = game_forward_up_vectors_to_bl_euler(Vector3(dummy.forward), Vector3(upward))
    t = Vector3(dummy.translate)
    if dummy.parent_bone_index == -1:
        return Matrix.LocRotScale(to_blender(t), bl_euler, (1.0, 1.0, 1.0))
    parent_t, parent_r = arma[bone_names[dummy.parent_bone_index]]
    t = Vector3((t[0] * parent_scale[0], t[1] * parent_scale[1], t[2] * parent_scale[2]))
    model_t = parent_t + parent_r @ t
    bl_parent_rot = to_blender(parent_r).to_4x4()
    return Matrix.Translation(to_blender(model_t)) @ bl_parent_rot @ bl_euler.to_matrix().to_4x4()


@T.register_bl_test(DUMMY_TESTS)
def test_dummy_placement_scaled_parent_bone():
    T.clear_scene()
    armature = _make_test_armature()
    # FLVER scale is stored on a custom property for EDIT bone data (Blender coordinates, i.e. game Y/Z swapped).
    armature.data.bones["Sfx"].FLVER_BONE.flver_scale = (3.5, 3.5, 3.5)
    dummy = _dummy(parent_bone_index=2, attach_bone_index=1)
    bl_dummy = _import_dummy(armature, dummy)
    bpy.context.view_layer.update()

    arma = _game_arma_transforms(BONE_DEFS, parents={})
    expected = _expected_world_from_game(arma, [b[0] for b in BONE_DEFS], dummy, parent_scale=(3.5, 3.5, 3.5))
    actual = bl_dummy.obj.matrix_world
    T.assert_true(
        _matrices_close(actual, expected),
        "test_dummy_placement_scaled_parent_bone",
        f"max component error {_max_matrix_diff(actual, expected):.6f} "
        f"(expected translation {tuple(round(v, 4) for v in expected.translation)}, "
        f"got {tuple(round(v, 4) for v in actual.translation)})",
    )
    # Scale must affect only the Dummy's location, not the Empty itself.
    T.assert_true(
        all(abs(s - 1.0) <= TOL for s in actual.to_scale()),
        "test_dummy_placement_scaled_parent_bone/no_empty_scale",
        f"Empty has scale {tuple(actual.to_scale())}",
    )

    exported = bl_dummy.to_soulstruct_obj(operator=None, context=bpy.context, armature=armature)
    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(exported.translate, dummy.translate)),
        "test_dummy_placement_scaled_parent_bone/roundtrip_translate",
        f"expected {tuple(dummy.translate)}, got {tuple(exported.translate)}",
    )


# ---------------------------------------------------------------------------
# Non-orthonormal FLVER vectors (most vanilla Dummies: e.g. |forward| ~0.12, |upward| ~0.05)
# ---------------------------------------------------------------------------

@T.register_bl_test(DUMMY_TESTS)
def test_dummy_orientation_unnormalized_vectors():
    T.clear_scene()
    armature = _make_test_armature()
    # Vanilla DeS c1030 Dummy: forward +X (length 0.12) and upward -Z (length 0.05).
    dummy = _dummy(parent_bone_index=-1, attach_bone_index=1)
    dummy.forward = Vector3((0.12064981460571289, 0.0, -3.725290298461914e-09))
    dummy.upward = Vector3((0.0, 0.0, -0.051689513027668))
    bl_dummy = _import_dummy(armature, dummy)
    bpy.context.view_layer.update()

    rot = bl_dummy.obj.matrix_world.to_3x3().normalized()
    for axis_index, game_vector, label in ((1, (1.0, 0.0, 0.0), "forward"), (2, (0.0, 0.0, -1.0), "upward")):
        # Blender local +Y is the game forward, local +Z is the game up (see `bl_rotmat_to_game_forward_up_vectors`).
        expected = to_blender(Vector3(game_vector))
        actual = rot.col[axis_index]
        T.assert_true(
            all(abs(a - b) <= TOL for a, b in zip(actual, expected)),
            f"test_dummy_orientation_unnormalized_vectors/{label}",
            f"expected {tuple(round(v, 4) for v in expected)}, got {tuple(round(v, 4) for v in actual)}",
        )


# ---------------------------------------------------------------------------
# CUSTOM bone data (static FLVERs: every weapon, some characters/objects, map pieces)
# ---------------------------------------------------------------------------

# LOCAL bone transforms for a CUSTOM armature, with a hierarchy: 'Child' is parented to 'Root'.
CUSTOM_BONE_DEFS = [
    ("Root", Vector3((0.2, -0.1, 0.3)), (0.3, 0.5, -0.2), 0.2),
    ("Child", Vector3((0.0, 0.4, 0.1)), (-0.6, 0.1, 0.9), 0.2),
    ("Sfx", Vector3((0.0, 0.0, 0.0)), (0.0, 0.0, 0.0), 0.2),
]
CUSTOM_PARENTS = {"Child": "Root"}


def _make_custom_test_armature() -> bpy.types.Object:
    """Build an Armature exactly as FLVER import does for CUSTOM bone data: EditBones are identity Y-forward stubs and
    FLVER LOCAL bone transforms are written to PoseBone channels (see `write_data_to_custom_bone_prop_and_pose()`)."""
    armature_data = bpy.data.armatures.new("TestStatic Armature")
    armature = bpy.data.objects.new("TestStatic Armature", armature_data)
    bpy.context.scene.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = {}
    for name, _t, _r, _length in CUSTOM_BONE_DEFS:
        edit_bone = armature_data.edit_bones.new(name)
        edit_bone.head = (0.0, 0.0, 0.0)
        edit_bone.tail = (0.0, 0.2, 0.0)
        edit_bone.use_local_location = True
        edit_bone.inherit_scale = "NONE"
        edit_bones[name] = edit_bone
    for child, parent in CUSTOM_PARENTS.items():
        edit_bones[child].parent = edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, translate, rotate_rad, _length in CUSTOM_BONE_DEFS:
        pose_bone = armature.pose.bones[name]
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.location = to_blender(translate)
        pose_bone.rotation_quaternion = to_blender(Matrix3.from_euler_angles_rad(rotate_rad)).to_quaternion()
    return armature


def _check_custom_placement(test_name: str, dummy: Dummy, sfx_scale: float = 1.0):
    T.clear_scene()
    armature = _make_custom_test_armature()
    if sfx_scale != 1.0:
        armature.pose.bones["Sfx"].scale = (sfx_scale, sfx_scale, sfx_scale)
    bl_dummy = BlenderFLVERDummy.new_from_soulstruct_obj(
        operator=None,
        context=bpy.context,
        soulstruct_obj=dummy,
        name=f"TestStatic Dummy<0> [{dummy.reference_id}]",
        armature=armature,
        collection=bpy.context.scene.collection,
        bone_data_type=FLVERBoneDataType.CUSTOM,
    )
    bpy.context.view_layer.update()

    arma = _game_arma_transforms(CUSTOM_BONE_DEFS, CUSTOM_PARENTS)
    scale = (sfx_scale,) * 3 if CUSTOM_BONE_DEFS[dummy.parent_bone_index][0] == "Sfx" else (1.0, 1.0, 1.0)
    expected = _expected_world_from_game(arma, [b[0] for b in CUSTOM_BONE_DEFS], dummy, parent_scale=scale)
    actual = bl_dummy.obj.matrix_world
    T.assert_true(
        _matrices_close(actual, expected),
        f"{test_name}/world_transform",
        f"max component error {_max_matrix_diff(actual, expected):.6f} "
        f"(expected translation {tuple(round(v, 4) for v in expected.translation)}, "
        f"got {tuple(round(v, 4) for v in actual.translation)})",
    )

    exported = bl_dummy.to_soulstruct_obj(
        operator=None, context=bpy.context, armature=armature, bone_data_type=FLVERBoneDataType.CUSTOM
    )
    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(exported.translate, dummy.translate)),
        f"{test_name}/roundtrip_translate", f"expected {tuple(dummy.translate)}, got {tuple(exported.translate)}",
    )
    T.assert_true(
        all(abs(a - b) <= TOL for a, b in zip(exported.forward, dummy.forward)),
        f"{test_name}/roundtrip_forward", f"expected {tuple(dummy.forward)}, got {tuple(exported.forward)}",
    )
    T.assert_equal(exported.parent_bone_index, dummy.parent_bone_index, f"{test_name}/parent_bone_index")
    T.assert_equal(exported.attach_bone_index, dummy.attach_bone_index, f"{test_name}/attach_bone_index")


@T.register_bl_test(DUMMY_TESTS)
def test_custom_dummy_placement_identity_parent_bone():
    """Every weapon: Dummies 'in space of' an identity bone. Undoing the (never-applied) bone CoB here swapped their X/Y
    and negated their Z."""
    _check_custom_placement(
        "test_custom_dummy_placement_identity_parent_bone", _dummy(parent_bone_index=2, attach_bone_index=-1)
    )


@T.register_bl_test(DUMMY_TESTS)
def test_custom_dummy_placement_child_parent_bone():
    _check_custom_placement(
        "test_custom_dummy_placement_child_parent_bone", _dummy(parent_bone_index=1, attach_bone_index=-1)
    )


@T.register_bl_test(DUMMY_TESTS)
def test_custom_dummy_placement_attach_bone():
    """Blender resolves a bone-parented Object against the POSED bone, which is where CUSTOM bone transforms live."""
    _check_custom_placement(
        "test_custom_dummy_placement_attach_bone", _dummy(parent_bone_index=0, attach_bone_index=1)
    )


@T.register_bl_test(DUMMY_TESTS)
def test_custom_dummy_placement_scaled_parent_bone():
    _check_custom_placement(
        "test_custom_dummy_placement_scaled_parent_bone",
        _dummy(parent_bone_index=2, attach_bone_index=1),
        sfx_scale=2.5,
    )


if __name__ == "__main__":
    T.run_tests(DUMMY_TESTS)
