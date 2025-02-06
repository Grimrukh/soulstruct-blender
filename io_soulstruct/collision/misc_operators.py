from __future__ import annotations

__all__ = [
    "RenameCollision",
    "CreateFromSelectedFLVERFaces",
    "SelectHiResFaces",
    "SelectLoResFaces",
]

from functools import lru_cache

import bmesh
import bpy

from soulstruct_havok.fromsoft.shared.map_collision import MapCollisionMaterial

from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.collision.utilities import HKX_MATERIAL_NAME_RE
from io_soulstruct.exceptions import SoulstructTypeError
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import get_collection_map_stem
from io_soulstruct.utilities.operators import LoggingOperator


class RenameCollision(LoggingOperator):
    """Simply renames a Collision model and all MSB Collision parts that instance it."""
    bl_idname = "object.rename_hkx_collision"
    bl_label = "Rename Collision"
    bl_description = (
        "Rename the selected Collision model and, optionally, the overlapping prefix of any MSB Collision part that "
        "instance it"
    )

    new_name: bpy.props.StringProperty(
        name="New Name",
        description="New name for the Collision model",
        default="",
    )
    rename_parts: bpy.props.BoolProperty(
        name="Rename Parts",
        description="Rename MSB Collision parts that instance this Collision model",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        try:
            BlenderMapCollision.from_active_object(context)
        except SoulstructTypeError:
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Rename Collision")

    def execute(self, context):
        if not self.new_name:
            return self.error("New Collision name cannot be empty.")

        collision = BlenderMapCollision.from_active_object(context)
        old_model_name = collision.tight_name
        new_model_name = self.new_name

        collision.name = new_model_name
        collision.data.name = new_model_name

        if self.rename_parts:
            part_count = 0
            for obj in bpy.data.objects:
                if (
                    obj.soulstruct_type == SoulstructType.MSB_PART
                    and obj.MSB_PART.part_subtype == "MSB_COLLISION"
                    and obj is not collision
                    and obj.data == collision.data
                ):
                    # Found a part to rename.
                    part_count += 1
                    old_part_name = obj.name
                    for i, (a, b) in enumerate(zip(old_part_name, old_model_name)):
                        if a != b:
                            new_part_prefix = new_model_name[:i]  # take same length prefix from new model name
                            new_part_suffix = old_part_name[i:]  # keep old Part suffix ('_0000', '_CASTLE', whatever).
                            obj.name = f"{new_part_prefix}{new_part_suffix}"
                            break
                    # No need for an `else` check because Blender object names cannot be identical.
            self.info(f"Renamed {part_count} MSB Collisions that instance '{old_model_name}' to '{new_model_name}'.")

        return {"FINISHED"}


# Ordered word lookups in FLVER material names.
# Note that the same value can appear multiple times to give it different word-based priorities.
# TODO: Add more words to this list as needed. It's actually a fairly small set of used words in FLVER materials.
_FLVER_WORDS_TO_HKX_MATERIAL = {
    ("_stone",): MapCollisionMaterial.Stone,
    ("_bridge_board", "_wood", "_tree"): MapCollisionMaterial.Wood,
    ("_ground", "_grass"): MapCollisionMaterial.Grass,
    ("_cliff", "_rock"): MapCollisionMaterial.Rock,
    ("_wall", "_floor"): MapCollisionMaterial.Stone,
}


@lru_cache(256)
def _flver_mat_name_to_hkx_mat_index(flver_mat_name: str) -> int:
    """NOTE: In vanilla, hi and lo-res collision materials are sometimes different.

    e.g. a clear grass FLVER material will be Grass in lo-res HKX, but just Rock in hi-res. This
    would presumably make footsteps grassy, but projectile impacts rocky. This returns a unified
    value for now (the most accurate).

    TODO: Only set up for generic words and some random specific words (DS1R) at the moment.

    TODO: Tree/plant FLVER materials that shouldn't have any collision should return something indicating that.
    """

    name = flver_mat_name.lower().split("[")[0].strip()

    for words, material in _FLVER_WORDS_TO_HKX_MATERIAL.items():
        for word in words:
            if word in name:
                return material

    return MapCollisionMaterial.Default  # so user can actually detect any misses


class CreateFromSelectedFLVERFaces(LoggingOperator):
    bl_idname = "object.hkx_from_selected_flver_faces"
    bl_label = "Create Collision from FLVER Faces"
    bl_description = (
        "Create a new collision object from the selected FLVER faces in the edited object. "
        "Uses an in-progress map from vanilla DS1R FLVER material names to HKX material indices. "
        "Unhandled FLVER materials will be mapped to default HKX material 0 (grey). NOTE: You don't have to use a "
        "FLVER-type object for this, but material names will attempt to map to collision materials based on FLVERs"
    )

    collision_model_name: bpy.props.StringProperty(
        name="Collision Model Name",
        description="Name for the new collision model. If empty, will just add ' Collision' to source model name",
        default="",
    )

    move_to_collision_collection: bpy.props.BoolProperty(
        name="Move to Collision Collection",
        description="If source model is in a collection called '{map_stem} Map Piece Models', create new collision "
                    "in collection called '{map_stem} Collision Models' if it exists (rather than same collection)",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Exactly one Mesh must be selected and in Edit mode."""
        return context.mode == "EDIT_MESH" and context.edit_object is not None and len(context.selected_objects) == 1

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Create Collision from FLVER")

    def execute(self, context):

        # noinspection PyTypeChecker
        source_mesh = context.edit_object  # type: bpy.types.MeshObject
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')

        # Switch to OBJECT mode and identify the newly created object.
        bpy.ops.object.mode_set(mode="OBJECT")

        # We know only one object was selected previously (from above) so the other must be it.
        try:
            # noinspection PyTypeChecker
            collision_mesh = [
                obj for obj in context.selected_objects
                if obj != source_mesh
            ][0]  # type: bpy.types.MeshObject
        except IndexError:
            return self.error("Could not identify collision mesh object produced by Mesh > Duplicate operator.")

        new_name = self.collision_model_name or f"{source_mesh.name} Collision"
        collision_mesh.name = new_name
        collision_mesh.data.name = new_name

        if self.move_to_collision_collection:
            try:
                map_stem = get_collection_map_stem(source_mesh)
            except ValueError:
                # Don't move collections.
                self.warning("Could not find map stem in source object's collection name. New collision not moved.")
            else:
                try:
                    collision_collection = bpy.data.collections[f"{map_stem} Collision Models"]
                except KeyError:
                    self.warning(f"Could not find collection '{map_stem} Collision Models'. New collision not moved.")
                else:
                    for collection in collision_mesh.users_collection:
                        collection.objects.unlink(collision_mesh)
                    collision_collection.objects.link(collision_mesh)

        # Deselect all, then select only collision_mesh.
        bpy.ops.object.select_all(action="DESELECT")
        collision_mesh.select_set(True)
        context.view_layer.objects.active = collision_mesh

        collision_mesh.soulstruct_type = SoulstructType.COLLISION

        # Switch to Edit mode on the collision object.
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(collision_mesh.data)

        old_material_count = len(collision_mesh.data.materials)

        # Process each face: assign the Hi material based on the original material’s name.
        for face in bm.faces:
            # Get the original material from the collision object's material slots.
            orig_mat = None
            if face.material_index < len(source_mesh.data.materials):
                orig_mat = source_mesh.data.materials[face.material_index]
            orig_mat_name = orig_mat.name if orig_mat else ""

            # Map the original material name to a collision index.
            collision_mat_index = _flver_mat_name_to_hkx_mat_index(orig_mat_name)

            mat_hi = BlenderMapCollision.get_hkx_material(collision_mat_index, is_hi_res=True)

            # Ensure the collision object uses this material.
            if collision_mesh.data.materials.find(mat_hi.name) == -1:
                collision_mesh.data.materials.append(mat_hi)
            # Set the face material to the Hi version.
            face.material_index = collision_mesh.data.materials.find(mat_hi.name) - old_material_count

        bm.free()
        del bm

        # Remove all materials from the collision object whose names do NOT start with "HKX".
        # We know none of these are used by the faces at this point.
        for _ in range(old_material_count):
            collision_mesh.data.materials.pop(index=0)

        # It's easier to save back the edit mesh, select it all, and duplicate it to get the identical 'Lo' version.
        bmesh.update_edit_mesh(collision_mesh.data)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.duplicate()

        # Use bmesh again to update the material on the duplicated (selected) faces to the low-resolution version.
        bm = bmesh.from_edit_mesh(collision_mesh.data)
        for face in bm.faces:
            if face.select:
                # Find 'Lo' version of same material.
                mat_name = collision_mesh.data.materials[face.material_index].name
                m = HKX_MATERIAL_NAME_RE.match(mat_name)
                index = int(m.group(1))

                mat_lo = BlenderMapCollision.get_hkx_material(index, is_hi_res=False)

                if collision_mesh.data.materials.find(mat_lo.name) == -1:
                    collision_mesh.data.materials.append(mat_lo)
                face.material_index = collision_mesh.data.materials.find(mat_lo.name)

        # Save updated lo-res materials to edit mesh.
        bmesh.update_edit_mesh(collision_mesh.data)

        bm.free()
        del bm

        bpy.ops.object.mode_set(mode='OBJECT')

        self.info(f"Collision Mesh model generated from '{source_mesh.name}': '{collision_mesh.name}'")

        return {"FINISHED"}


class SelectHiResFaces(LoggingOperator):
    bl_idname = "object.select_hi_res_faces"
    bl_label = "Select Hi-Res Collision Faces"
    bl_description = "Select all hi-res collision faces (materials with '(Hi)') in the edited object"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.edit_object is not None

    def execute(self, context):
        bpy.ops.mesh.select_all(action="DESELECT")
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject
        bpy.ops.object.mode_set(mode="OBJECT")
        if obj.type != "MESH":
            return self.error("Selected object is not a mesh.")
        for face in obj.data.polygons:
            if "(Hi)" in obj.data.materials[face.material_index].name:
                face.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class SelectLoResFaces(LoggingOperator):
    bl_idname = "object.select_lo_res_faces"
    bl_label = "Select Lo-Res Collision Faces"
    bl_description = "Select all lo-res collision faces (materials with '(Lo)') in the edited object"

    @classmethod
    def poll(cls, context) -> bool:
        return context.mode == "EDIT_MESH" and context.edit_object is not None

    def execute(self, context):
        bpy.ops.mesh.select_all(action="DESELECT")
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: bpy.types.MeshObject
        bpy.ops.object.mode_set(mode="OBJECT")
        if obj.type != "MESH":
            return self.error("Selected object is not a mesh.")
        for face in obj.data.polygons:
            if "(Lo)" in obj.data.materials[face.material_index].name:
                face.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}
