from __future__ import annotations

__all__ = [
    "PrintGameTransform",
    "DummyInfo",
    "parse_dummy_name",
    "parse_flver_obj",
    "get_default_flver_stem",
    "get_selected_flver",
    "get_selected_flvers",
    "replace_name_model",
    "rename_flver",
    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "get_flvers_from_binder",
    "get_map_piece_msb_transforms",
    "game_forward_up_vectors_to_bl_euler",
    "bl_euler_to_game_forward_up_vectors",
    "bl_rotmat_to_game_forward_up_vectors",
]

import re
import typing as tp
from pathlib import Path

import bpy
from mathutils import Euler, Matrix

from soulstruct import Binder, FLVER
from soulstruct.utilities.maths import Vector3, Matrix3
from soulstruct.darksouls1r.maps import MSB, get_map

from io_soulstruct.exceptions import *
from io_soulstruct.utilities import (
    Transform, BlenderTransform, GAME_TO_BL_EULER, BL_TO_GAME_EULER, BL_TO_GAME_MAT3, LoggingOperator
)
from io_soulstruct.general.cached import get_cached_file


_BLENDER_DUPE_RE = re.compile(r"^(.*)\.(\d+)$")


class HideAllDummiesOperator(LoggingOperator):
    """Simple operator to hide all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.hide_all_dummies"
    bl_label = "Hide All Dummies"
    bl_description = "Hide all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        armature = context.selected_objects[0]
        for child in armature.children:
            if child.type == "EMPTY" and "dummy" in child.name.lower():
                child.hide_viewport = True
        return {"FINISHED"}


class ShowAllDummiesOperator(LoggingOperator):
    """Simple operator to show all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.show_all_dummies"
    bl_label = "Show All Dummies"
    bl_description = "Show all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        armature = context.selected_objects[0]
        for child in armature.children:
            if child.type == "EMPTY" and "dummy" in child.name.lower():
                child.hide_viewport = False
        return {"FINISHED"}


class PrintGameTransform(LoggingOperator):
    """Simple operator that prints the Blender transform of a selected object to console in game coordinates."""
    bl_idname = "io_scene_soulstruct.print_game_transform"
    bl_label = "Print Game Transform"
    bl_description = "Print the selected object's transform in game coordinates to Blender console"

    @classmethod
    def poll(cls, context):
        return context.object is not None

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        obj = context.object
        if obj:
            bl_transform = BlenderTransform(obj.location, obj.rotation_euler, obj.scale)
            print(
                f"FromSoftware game transform of object '{obj.name}':\n"
                f"    translate = {repr(bl_transform.game_translate)}\n"
                f"    rotate = {repr(bl_transform.game_rotate_deg)}  # degrees\n"
                f"    scale = {repr(bl_transform.game_scale)}"
            )
        return {"FINISHED"}


DUMMY_NAME_RE = re.compile(  # accepts and ignores Blender '.001' suffix and anything else after the `[ref_id]` in name
    r"^(?P<model_name>.+ *[ |])?[Dd]ummy(?P<index><\d+>)? *(?P<reference_id>\[\d+\]) *(\.\d+)?$"
)


class DummyInfo(tp.NamedTuple):
    model_name: str
    reference_id: int


def parse_dummy_name(dummy_name: str) -> DummyInfo | None:
    """Validate a FLVER dummy object name and return its extracted `model_name` (optional) and `reference_id`.

    The index in the dummy name is not used or required - it is only created by the importer to preserve the order of
    dummies by default.

    If the dummy name is invalid, `None` is returned.
    """
    match = DUMMY_NAME_RE.match(dummy_name)
    if not match:
        return None  # invalid name
    model_name = match.group("model_name")  # could be None
    if model_name:
        model_name = model_name.rstrip(" |")
    return DummyInfo(
        model_name=model_name,
        reference_id=int(match.group("reference_id")[1:-1]),  # exclude brackets in regex group
    )


def parse_flver_obj(obj: bpy.types.Object) -> tuple[bpy.types.MeshObject, bpy.types.ArmatureObject | None]:
    """Parse a Blender object into a Mesh and (optional) Armature object."""
    if obj.type == "MESH":
        mesh = obj
        armature = mesh.parent if mesh.parent is not None and mesh.parent.type == "ARMATURE" else None
    elif obj.type == "ARMATURE":
        armature = obj
        mesh_name = f"{obj.name} Mesh"
        mesh_children = [child for child in armature.children if child.type == "MESH" and child.name == mesh_name]
        if not mesh_children:
            raise FLVERExportError(
                f"Armature '{armature.name}' has no Mesh child '{mesh_name}'. Please create it, even if empty, "
                f"and assign it any required FLVER custom properties such as 'Version', 'Unicode', etc."
            )
        mesh = mesh_children[0]
    else:
        raise FLVERExportError(f"Selected object '{obj.name}' is not a Mesh or Armature.")

    return mesh, armature


def get_default_flver_stem(
    mesh: bpy.types.MeshObject, armature: bpy.types.ArmatureObject = None, operator: LoggingOperator = None
) -> str:
    """Returns the name that should be used (by default) for the exported FLVER, warning if the Mesh and Armature
    objects have different names."""
    name = mesh.name.split(".")[0].split(" ")[0]
    if armature is not None and (armature_name := armature.name.split(" ")[0]) != name:
        if operator:
            operator.warning(
                f"Mesh '{name}' and Armature '{armature_name}' do not use the same FLVER name. Using Armature name."
            )
        return armature_name
    return name


def get_selected_flver(context) -> tuple[bpy.types.MeshObject, bpy.types.ArmatureObject | None]:
    """Get the Mesh and (optional) Armature components of a single selected FLVER object of either type."""
    if not context.selected_objects:
        raise FLVERError("No FLVER Mesh or Armature selected.")
    elif len(context.selected_objects) > 1:
        raise FLVERError("Multiple objects selected. Exactly one FLVER Mesh or Armature must be selected.")
    obj = context.selected_objects[0]
    return parse_flver_obj(obj)


def get_selected_flvers(context) -> list[tuple[bpy.types.MeshObject, bpy.types.ArmatureObject | None]]:
    """Get the Mesh and (optional) Armature components of ALL selected FLVER objects of either type."""
    if not context.selected_objects:
        raise FLVERError("No FLVER Meshes or Armatures selected.")
    return [parse_flver_obj(obj) for obj in context.selected_objects]


def get_flvers_from_binder(binder: Binder, file_path: Path, allow_multiple=False) -> list[FLVER]:
    flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
    if not flver_entries:
        raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
    elif not allow_multiple and len(flver_entries) > 1:
        raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}.")
    return [entry.to_binary_file(FLVER) for entry in flver_entries]


def replace_name_model(
    name: str,
    old_model_name: str,
    new_model_name: str,
    strip_dupe_suffix=True,
) -> str:
    if strip_dupe_suffix and (match := _BLENDER_DUPE_RE.match(name)):
        name = match.group(1)
    if name.startswith(old_model_name):
        return f"{new_model_name}{name.removeprefix(old_model_name)}"
    if name.endswith(f"| {old_model_name}]"):
        # Standard material endings.
        return name.replace(f"| {old_model_name}]", f"| {new_model_name}]")
    return name

def rename_flver(
    armature: bpy.types.ArmatureObject,
    mesh: bpy.types.MeshObject,
    old_name: str,
    new_name: str,
    strip_dupe_suffix=True,
    rename_func: tp.Callable[[str, str], str] = None,
):
    """Rename all components of given FLVER object (Armature, Mesh, materials, bones, dummies) using `rename` function
    or a standard default. Can also strip Blender's duplicate suffix, e.g. '.001', which it does by default."""

    if rename_func is None:
        def rename(name: str):
            return replace_name_model(name, old_name, new_name, strip_dupe_suffix=strip_dupe_suffix)
    else:
        # Partial of given `rename_func`.
        def rename(name: str):
            return rename_func(name, new_name)

    mesh.name = rename(mesh.name)
    mesh.data.name = rename(mesh.data.name)
    for mat in mesh.data.materials:
        mat.name = rename(mat.name)

    if armature:
        armature.name = rename(armature.name)
        armature.data.name = rename(armature.data.name)
        bone_renaming = {}
        for bone in armature.data.bones:
            old_bone_name = bone.name
            bone.name = bone_renaming[old_bone_name] = rename(bone.name)
        for vertex_group in mesh.vertex_groups:
            if vertex_group.name in bone_renaming:
                vertex_group.name = bone_renaming[vertex_group.name]
        dummy_prefix = f"{old_name} Dummy"
        for child in armature.children:
            if child.type == "EMPTY" and child.name.startswith(dummy_prefix):
                child.name = rename(child.name)
                child["Parent Bone Name"] = rename(child["Parent Bone Name"])


def get_map_piece_msb_transforms(flver_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `flver_path.parent` by default) and return
    `(map_piece_name, Transform)` pairs for all Map Piece entries using the `flver_path` model.

    Uses cached MSB if possible.

    TODO: Use settings game directory rather than guessing from FLVER path, if possible.
    """
    if msb_path is None:
        flver_parent_dir = flver_path.parent
        flver_map = get_map(flver_parent_dir.name)
        msb_path = flver_parent_dir.parent / f"MapStudio/{flver_map.msb_file_stem}.msb"
    if not msb_path.is_file():
        raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
    try:
        msb = get_cached_file(msb_path, MSB)
    except Exception as ex:
        raise RuntimeError(
            f"Cannot open MSB: {ex}.\n"
            f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
        )
    matches = []
    for map_piece in msb.map_pieces:
        if flver_path.name.startswith(map_piece.model.name):
            matches.append(map_piece)
    if not matches:
        raise ValueError(f"Cannot find any MSB Map Piece entries using model '{flver_path.name}'.")
    transforms = [(m.name, Transform.from_msb_entry(m)) for m in matches]
    return transforms


def game_forward_up_vectors_to_bl_euler(forward: Vector3, up: Vector3) -> Euler:
    """Convert `forward` and `up` vectors to Euler angles `(x, y, z)` (in Blender coordinates).

    Mainly used for representing FLVER dummies in Blender.
    """
    right = up.cross(forward)
    rotation_matrix = Matrix3([
        [right.x, up.x, forward.x],
        [right.y, up.y, forward.y],
        [right.z, up.z, forward.z],
    ])
    game_euler = rotation_matrix.to_euler_angles(radians=True)
    return GAME_TO_BL_EULER(game_euler)


def bl_euler_to_game_forward_up_vectors(bl_euler: Euler) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Euler` to its forward-axis and up-axis vectors in game space (for `FLVER.Dummy`)."""
    game_euler = BL_TO_GAME_EULER(bl_euler)
    game_mat = Matrix3.from_euler_angles(game_euler)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


def bl_rotmat_to_game_forward_up_vectors(bl_rotmat: Matrix) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Matrix` to its game equivalent's forward-axis and up-axis vectors (for `FLVER.Dummy`)."""
    game_mat = BL_TO_GAME_MAT3(bl_rotmat)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up
