from __future__ import annotations

__all__ = [
    "RenameCollision",
    "GenerateFromMesh",
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
from io_soulstruct.utilities import get_collection_map_stem, replace_shared_prefix
from io_soulstruct.utilities.operators import LoggingOperator


class RenameCollision(LoggingOperator):
    """Simply renames a Collision model and all MSB Collision/Connect Collision parts that instance it."""
    bl_idname = "object.rename_hkx_collision"
    bl_label = "Rename Collision"
    bl_description = (
        "Rename the selected Collision model and, optionally, the overlapping prefix of any MSB Collision or Connect "
        "Collision part that instances it"
    )

    new_name: bpy.props.StringProperty(
        name="New Name",
        description="New name for the Collision model",
        default="",
    )
    rename_parts: bpy.props.BoolProperty(
        name="Rename Parts",
        description="Rename MSB Collision and Connect Collision parts that instance this Collision model",
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
                    and obj.MSB_PART.part_subtype in {"MSB_COLLISION", "MSB_CONNECT_COLLISION"}
                    and obj is not collision
                    and obj.data == collision.data
                ):
                    # Found a part to rename.
                    part_count += 1
                    obj.name = replace_shared_prefix(old_model_name, new_model_name, obj.name)
            self.info(
                f"Renamed {part_count} MSB Collisions/Connect Collisions that instance "
                f"'{old_model_name}' to '{new_model_name}'."
            )

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


class GenerateFromMesh(LoggingOperator):
    bl_idname = "object.generate_collision_from_mesh"
    bl_label = "Create Collision from Mesh"
    bl_description = (
        "Create a new Collision model object from all selected faces in all currently edited meshes. Will also "
        "attempt to automatically assign collision materials based on FLVER material names (defaulting to 0)"
    )

    collision_model_name: bpy.props.StringProperty(
        name="Collision Model Name",
        description="Name for the new collision model. If empty, will just add ' Collision' to first source model name",
        default="",
    )

    move_to_collision_collection: bpy.props.BoolProperty(
        name="Move to Collision Collection",
        description="If any source model is in a collection called '{map_stem} Map Piece Models', create new collision "
                    "in collection called '{map_stem} Collision Models' if it exists (rather than same collection)",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Must be in Edit mode (editing meshes), and edited objects must be exactly the selected objects.

        Otherwise it's too annoying to detect the duplicated objects.
        """
        edited_names = {obj.name for obj in context.objects_in_mode_unique_data}
        selected_names = {obj.name for obj in context.selected_objects}
        return (
            context.mode == "EDIT_MESH"
            and edited_names
            and edited_names == selected_names
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, title="Create Collision from FLVER")

    def execute(self, context):

        # noinspection PyTypeChecker
        source_meshes = context.objects_in_mode  # type: list[bpy.types.MeshObject]
        if any(obj.type != "MESH" for obj in source_meshes):
            return self.error("All objects being edited must be meshes.")

        # Duplicate whatever faces are currently selected.
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')

        # Switch to OBJECT mode and identify the newly created objects.
        bpy.ops.object.mode_set(mode="OBJECT")
        # We just remove the objects that were selected before, in edit mode, leaving only the new objects.
        new_objs = [obj for obj in context.selected_objects if obj not in source_meshes]
        if len(new_objs) != len(source_meshes):
            return self.error(
                f"Could not identify {len(source_meshes)} new collision mesh objects produced by Mesh > Separate. "
                f"New meshes may still have been created."
            )

        # Select just the new objects and join them (to the first).
        bpy.ops.object.select_all(action="DESELECT")
        for obj in new_objs:
            obj.select_set(True)
        context.view_layer.objects.active = new_objs[0]  # join target
        bpy.ops.object.join()
        # noinspection PyTypeChecker
        new_model = new_objs[0]  # type: bpy.types.MeshObject

        new_name = self.collision_model_name or f"{source_meshes[0].name} Collision"
        new_model.name = new_name
        new_model.data.name = new_name
        new_model.soulstruct_type = SoulstructType.COLLISION

        if self.move_to_collision_collection:
            try:
                map_stem = get_collection_map_stem(source_meshes[0])
            except ValueError:
                # Don't move to a new collection.
                self.warning(
                    "Could not find map stem in first source object's collection name. New collision not moved."
                )
            else:
                try:
                    collision_collection = bpy.data.collections[f"{map_stem} Collision Models"]
                except KeyError:
                    self.warning(f"Could not find collection '{map_stem} Collision Models'. New collision not moved.")
                else:
                    for collection in new_model.users_collection:
                        collection.objects.unlink(new_model)
                    collision_collection.objects.link(new_model)

        # Switch to Edit mode on the collision object.
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(new_model.data)

        old_material_count = len(new_model.data.materials)

        # Process each face: assign the Hi material based on the original material’s name.
        for face in bm.faces:
            # Get the original material from the collision object's material slots.
            orig_mat = None
            if face.material_index < len(new_model.data.materials):
                orig_mat = new_model.data.materials[face.material_index]
            orig_mat_name = orig_mat.name if orig_mat else ""

            # Map the original material name to a collision index.
            collision_mat_index = _flver_mat_name_to_hkx_mat_index(orig_mat_name)

            mat_hi = BlenderMapCollision.get_hkx_material(collision_mat_index, is_hi_res=True)

            # Ensure the collision object uses this material.
            if new_model.data.materials.find(mat_hi.name) == -1:
                new_model.data.materials.append(mat_hi)
            # Set the face material to the Hi version. We offset the material index in anticipation of all old
            # materials being removed. TODO: This will create problems if HKX materials already existed in source.
            face.material_index = new_model.data.materials.find(mat_hi.name) - old_material_count

        bm.free()
        del bm

        # Remove all materials from the collision object whose names do NOT start with "HKX".
        # We know none of these are used by the faces at this point.
        for _ in range(old_material_count):
            new_model.data.materials.pop(index=0)

        # It's easier to save back the edit mesh, select it all, and duplicate it to get the identical 'Lo' version.
        bmesh.update_edit_mesh(new_model.data)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.duplicate()

        # Use bmesh again to update the material on the duplicated (selected) faces to the low-resolution version.
        bm = bmesh.from_edit_mesh(new_model.data)
        for face in bm.faces:
            if face.select:
                # Find 'Lo' version of same material.
                mat_name = new_model.data.materials[face.material_index].name
                m = HKX_MATERIAL_NAME_RE.match(mat_name)
                index = int(m.group(1))

                mat_lo = BlenderMapCollision.get_hkx_material(index, is_hi_res=False)

                if new_model.data.materials.find(mat_lo.name) == -1:
                    new_model.data.materials.append(mat_lo)
                face.material_index = new_model.data.materials.find(mat_lo.name)

        # Save updated lo-res materials to edit mesh.
        bmesh.update_edit_mesh(new_model.data)

        bm.free()
        del bm

        bpy.ops.object.mode_set(mode='OBJECT')

        source_names = ", ".join(obj.name for obj in source_meshes)
        self.info(f"Collision Mesh model generated from {source_names}: '{new_model.name}'")

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
