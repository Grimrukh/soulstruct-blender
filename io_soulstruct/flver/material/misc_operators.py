"""Material operators."""
from __future__ import annotations

__all__ = [
    "MaterialToolSettings",
    "SetMaterialTexture0",
    "SetMaterialTexture1",
    "AutoRenameMaterials",
    "MergeFLVERMaterials",
    "AddMaterialGXItem",
    "RemoveMaterialGXItem",
]

import os
import re
import typing as tp
from pathlib import Path

import bpy

from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities.operators import LoggingOperator
from .types import BlenderFLVERMaterial

_AREA_PREFIX_RE = re.compile(r"m\d\d_")


class MaterialToolSettings(bpy.types.PropertyGroup):
    """Miscellaneous settings used by various Material operators."""

    albedo_image: bpy.props.PointerProperty(
        name="Albedo Image",
        type=bpy.types.Image,
    )

    use_model_stem_in_material_name: bpy.props.BoolProperty(
        name="Use Model Stem in Material Name",
        description="Include the model stem in the auto-generated material name (if no other FLVERs use it). Can "
                    "easily exceed 63-chr limit",
        default=False,
    )

    # TODO: These are currently unused. Can unify my two Material renaming operators:
    #   - Hash all materials in data
    #   - Scan all materials of all selected FLVERs
    #   - Can rename and/or merge materials independently
    #   - Can indicate whether hashing includes face set count in operator settings

    clean_up_identical: bpy.props.BoolProperty(
        name="Clean Up Identical",
        description="If the material with the auto-generated name already exists and is identical to the one on this "
                    "object, change this material to the existing one rather than renaming",
        default=True,
    )

    clean_up_ignores_face_set_count: bpy.props.BoolProperty(
        name="Clean Up Ignores Face Set Count",
        description="Ignore material (FLVER mesh) Face Set Count when considering identical materials",
        default=False,
    )


class _SetMaterialTexture(LoggingOperator):

    SLOT_SUFFIX: tp.ClassVar[str]

    @classmethod
    def poll(cls, context) -> bool:
        """An object must be selected."""
        return context.object is not None and context.object.active_material is not None

    def execute(self, context):
        return self.set_textures(context, self.SLOT_SUFFIX)

    def set_textures(self, context, slot_suffix: str):
        # Get selected material of selected object.
        selected_object = context.object
        if not selected_object:
            return self.error("No object selected.")
        selected_material = selected_object.active_material
        if not selected_material:
            return self.error("No material selected.")

        tool_settings = context.scene.material_tool_settings
        albedo_image = tool_settings.albedo_image
        if not albedo_image:
            return self.error("No albedo image selected.")

        # Try to find specular and normal images with "_s" and "_n" suffixes, respectively.
        albedo_image_name = albedo_image.name
        # Split name into stem and suffix.
        stem, suffix = albedo_image_name.rsplit(".", 1)
        # TODO: Game-dependent specular/normal suffixes, and also sheen.
        specular_image_name = f"{stem}_s.{suffix}"
        normal_image_name = f"{stem}_n.{suffix}"

        # These could be None. We still set them to the nodes.
        specular_image = bpy.data.images.get(specular_image_name)
        if not specular_image:
            self.warning(f"No specular texture named '{specular_image_name} found. Node image will be removed.")
        normal_image = bpy.data.images.get(normal_image_name)
        if not normal_image:
            self.warning(f"No normal texture named '{normal_image_name} found. Node image will be removed.")

        nodes = selected_material.node_tree.nodes
        for common_type, image in zip(["ALBEDO", "SPECULAR", "NORMAL"], [albedo_image, specular_image, normal_image]):
            node_name = f"{common_type}{slot_suffix}"
            try:
                node = nodes[node_name]
            except KeyError:
                self.warning(
                    f"No node named '{node_name}' found in material. Texture not {'set' if image else 'removed'}."
                )
            else:
                node.image = image

        return {"FINISHED"}


class SetMaterialTexture0(_SetMaterialTexture):

    bl_idname = "object.set_material_texture_0"
    bl_label = "Set Material Texture 0"
    bl_description = ("Set the first diffuse texture (e.g. 'g_Diffuse' in DS1) of the selected material to the "
                      "selected texture. Will attempt to set specular and normal textures as well, if nodes exist")

    SLOT_SUFFIX = "_0"


class SetMaterialTexture1(_SetMaterialTexture):

    bl_idname = "object.set_material_texture_1"
    bl_label = "Set Material Texture 1"
    bl_description = ("Set the second diffuse texture (e.g. 'g_Diffuse_2' in DS1) of the selected material to the "
                      "selected texture. Will attempt to set specular and normal textures as well, if nodes exist")

    SLOT_SUFFIX = "_1"


class AutoRenameMaterials(LoggingOperator):
    """TODO: Support other games."""

    bl_idname = "object.auto_rename_materials"
    bl_label = "Auto Rename Materials"
    bl_description = (
        "Automatically rename all materials of active FLVER model based on their texture names, index, "
        "and MatDef path. If the same target name exists multiple times, Blender's dupe suffix system will handle it "
        "e.g. '.001'). Currently only for DS1 FLVERs"
    )

    @classmethod
    def poll(cls, context) -> bool:
        settings = context.scene.soulstruct_settings
        if not settings.is_game_ds1():
            return False
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and obj.soulstruct_type == SoulstructType.FLVER

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.active_object  # type: bpy.types.MeshObject

        for i, material in enumerate(obj.data.materials):
            flver_material = BlenderFLVERMaterial(material)
            new_name = MergeFLVERMaterials.get_merged_material_name(flver_material)
            material.name = new_name  # will add dupe suffix if necessary

        return {"FINISHED"}


class MergeFLVERMaterials(LoggingOperator):
    """Scan all materials on all selected objects, and merge materials determined to be identical.

    See `get_material_hash` for rules on what makes two materials identical.

    NOTE: Shaders that use lightmap textures ('L') will probably make all Map Piece material users unique. This won't
    have much merging success if there are lots of lightmap users.
    """
    bl_idname = "object.merge_flver_materials"
    bl_label = "Merge FLVER Materials"
    bl_description = (
        "Look for identical FLVER materials across all selected objects and merge them into one Material "
        "instance (e.g. for easier texture management). New materials are named based on their diffuse textures, "
        "shader stem, backface culling (BC), and flags (<N>). Optionally, found materials can be renamed using this "
        "template even if no repeat uses are detected in the selection. Other than this optional renaming, no "
        "materials are changed or deleted; it is up to the user to clean up unused materials (i.e. those replaced with "
        "a new merged material) as desired"
    )

    rename_unique_materials: bpy.props.BoolProperty(
        name="Rename Unique Materials",
        description="Rename materials using merged template even if they are not merged with any other materials",
        default=True,
    )

    @classmethod
    def poll(cls, context) -> bool:
        if len(context.selected_objects) < 2:
            return False
        return all(
            obj.type == "MESH" and obj.soulstruct_type == SoulstructType.FLVER for obj in context.selected_objects
        )

    def execute(self, context):
        selected_objects = context.selected_objects

        # noinspection PyTypeChecker
        flver_objects = [
            obj for obj in selected_objects
            if obj.type == "MESH" and obj.soulstruct_type == SoulstructType.FLVER
        ]  # type: list[bpy.types.MeshObject]
        if len(flver_objects) < 2:
            return self.error("At least two FLVER Mesh model objects must be selected.")

        # Maps material hashes to their single merged instances (copied from first instance found).
        merged_materials = {}
        # Merged material created if it already appears in this set.
        found_materials = {}

        # Store all material hashes for all objects. List index will be used to replace `obj.data.materials[i]` later.
        all_obj_material_hashes = {}  # type: dict[str, list[int]]

        # First, build all material hashes and create merged materials whenever a hash is found for the second time.
        for obj in flver_objects:
            obj_material_hashes = all_obj_material_hashes.setdefault(obj.name, [])
            for material in obj.data.materials:
                if not material:
                    continue  # empty slot
                flver_material = BlenderFLVERMaterial(material)
                material_hash = self.get_material_hash(flver_material)
                obj_material_hashes.append(material_hash)

                if material_hash in merged_materials:
                    continue  # merged material already created; will be replaced in second pass
                if material_hash in found_materials:
                    # Create merged material.
                    merged_materials[material_hash] = merged_material = material.copy()
                    merged_material.name = self.get_merged_material_name(flver_material)
                    self.info(f"Created merged material: {merged_material.name}")
                    continue

                # Hash found for the first time. We store the material in case we still want to rename it below.
                found_materials[material_hash] = material

        # Now replace all appropriate materials with merged materials.
        for obj in flver_objects:
            for i, material_hash in enumerate(all_obj_material_hashes[obj.name]):
                if material_hash in merged_materials:
                    # Replace material `i`.
                    obj.data.materials[i] = merged_materials[material_hash]

        if self.rename_unique_materials:
            for material_hash, material in found_materials.items():
                if material_hash in merged_materials:
                    continue  # merged material was created above
                # This is a unique material that was not merged with any other material. We rename it anyway as asked.
                material.name = self.get_merged_material_name(BlenderFLVERMaterial(material))

        self.info(f"Created {len(merged_materials)} merged materials across {len(flver_objects)} objects.")

        return {"FINISHED"}

    @staticmethod
    def get_merged_material_name(material: BlenderFLVERMaterial) -> str:
        """We 'factor out' any shared prefix of all diffuse texture names, then add MatDef stem, <BC>, and <flags>.

        As materials have a 63-character name limit, this does the best job it can to keep the name informative. If we
        hit that name limit, the name will appear truncated (but Blender dupe suffix will keep conflicting material
        hashes separate).

        Example material name: `m14_(n_wall_10|b_ground_12) <M[DB][M]> <BC> <345>`
        """
        texture_name_dict = material.get_texture_name_dict()
        texture_names = []
        for sampler_name in ("g_Diffuse", "g_Diffuse_2"):
            if sampler_name in texture_name_dict:
                texture_name = texture_name_dict[sampler_name].split(".")[0]
                texture_names.append(texture_name)
        if len(texture_names) >= 2:
            shared_prefix = os.path.commonprefix(texture_names)
            if shared_prefix and "_" in shared_prefix:
                # Last character of shared prefix must be an underscore. Split back to that.
                shared_prefix = shared_prefix.rsplit("_", 1)[0] + "_"
                texture_names = [name[len(shared_prefix):] for name in texture_names]
                mat_name = f"{shared_prefix}({'|'.join(texture_names)})"  # e.g. "m14_(n_wall_10|b_ground_12)"
            else:
                mat_name = "|".join(texture_names)
        elif texture_names:
            mat_name = texture_names[0]
        else:
            mat_name = "No Diffuse"

        mat_name += f" <{Path(material.mat_def_path).stem}"

        if not material.use_backface_culling:
            mat_name += "|NBC"  # culling is way more common
        if material.flags:
            mat_name += f"|{material.flags}"
        mat_name += ">"

        return mat_name

    @staticmethod
    def get_material_hash(material: BlenderFLVERMaterial) -> int:
        """Hash all FLVER material properties and texture names.

        Rules for hash equality:
            - All `FLVER_MATERIAL` properties must be the same, including "face_set_count".
            - `use_backface_culling` must be the same.
            - All texture slots AND names must be the same.
            - Any materials with ANY GXItems are considered different. TODO: Not that hard to check, though.
        """
        hash_list = [material.use_backface_culling]

        for mat_prop in (
            "flags",
            "mat_def_path",
            "f2_unk_x18",
            "is_bind_pose",
            "default_bone_index",
            "face_set_count",
        ):
            hash_list.append(getattr(material, mat_prop))

        for sampler_name, texture_name in material.get_texture_name_dict().items():
            hash_list.append((sampler_name, texture_name))

        return hash(tuple(hash_list))


class AddMaterialGXItem(bpy.types.Operator):
    bl_idname = "material.add_gx_item"
    bl_label = "Add GX Item"
    bl_description = "Add a new GX Item to the active material"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None and context.active_object.active_material is not None

    def execute(self, context):
        material = context.active_object.active_material
        material.FLVER_MATERIAL.gx_items.add()
        return {"FINISHED"}


class RemoveMaterialGXItem(bpy.types.Operator):
    bl_idname = "material.remove_gx_item"
    bl_label = "Remove GX Item"
    bl_description = "Remove the selected GX Item from the active material"

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.active_object is not None
            and context.active_object.active_material is not None
            and len(context.active_object.active_material.FLVER_MATERIAL.gx_items) > 0
            and context.active_object.active_material.FLVER_MATERIAL.gx_item_index != -1
        )

    def execute(self, context):
        material = context.active_object.active_material
        index = material.FLVER_MATERIAL.gx_item_index
        material.FLVER_MATERIAL.gx_items.remove(index)
        material.FLVER_MATERIAL.gx_item_index = max(0, index - 1)
        return {"FINISHED"}


# TODO:
#   - Material Creator (dropdown of basic known MTD names like 'M[DB][M]')
