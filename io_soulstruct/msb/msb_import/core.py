from __future__ import annotations

__all__ = [
    "MissingModelError",
    "find_flver_model",
    "create_flver_model_instance",
    "msb_entry_to_obj_transform",
]

import typing as tp
import bpy

from io_soulstruct.utilities import Transform

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb.parts import BaseMSBPart
    from soulstruct.base.maps.msb.regions import BaseMSBRegion


class MissingModelError(Exception):
    """Raised when a model file cannot be found in a Blender collection."""


def find_flver_model(model_type: str, model_name: str) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Find the model of the given type in a 'Models' collection in the current scene."""
    try:
        collection = bpy.data.collections[f"{model_type} Models"]
    except KeyError:
        raise MissingModelError(f"Collection '{model_type} Models' not found in current scene.")
    for obj in collection.objects:
        if obj.name == model_name:
            if obj.type == "ARMATURE":
                mesh_obj = next((child for child in obj.children if child.type == "MESH"), None)
                if not mesh_obj:
                    raise MissingModelError(f"Armature '{model_name}' has no child mesh object.")
                return obj, mesh_obj
            elif obj.type == "MESH":  # Map Piece with no armature (acceptable)
                return None, obj
    raise MissingModelError(f"Model '{model_name}' not found in '{model_type} Models' collection.")


def create_flver_model_instance(
    context,
    armature: bpy.types.ArmatureObject | None,
    mesh: bpy.types.MeshObject,
    linked_name: str,
    collection: bpy.types.Collection,
) -> tuple[bpy.types.ArmatureObject | None, bpy.types.MeshObject]:
    """Create armature (optional) and mesh objects that link to the given armature and mesh data.

    NOTE: Does NOT copy dummy children from the source model. These aren't needed for linked MSB part instances, and
    will be found in the source model when exported (using 'Model Name') if needed. (Of course, Map Pieces in early
    games don't have dummies anyway.)
    """

    linked_mesh_obj = bpy.data.objects.new(f"{linked_name} Mesh", mesh.data)
    collection.objects.link(linked_mesh_obj)
    linked_mesh_obj["Model Name"] = mesh.name  # used by exporter to find FLVER properties

    if armature:
        linked_armature_obj = bpy.data.objects.new(linked_name, armature.data)
        collection.objects.link(linked_armature_obj)
        # Parent mesh to armature. This is critical for proper animation behavior (especially with root motion).
        linked_mesh_obj.parent = linked_armature_obj
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")
        linked_mesh_obj.select_set(True)
        context.view_layer.objects.active = linked_mesh_obj
        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = linked_mesh_obj.modifiers["Armature"]
        armature_mod.object = linked_armature_obj
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True
        # noinspection PyTypeChecker
        return linked_armature_obj, linked_mesh_obj

    # noinspection PyTypeChecker
    return None, linked_mesh_obj



def msb_entry_to_obj_transform(msb_entry: BaseMSBPart | BaseMSBRegion, obj: bpy.types.Object):
    game_transform = Transform.from_msb_entry(msb_entry)
    obj.location = game_transform.bl_translate
    obj.rotation_euler = game_transform.bl_rotate
    obj.scale = game_transform.bl_scale
