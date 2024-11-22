"""Material operators."""
from __future__ import annotations

__all__ = [
    "MaterialToolSettings",
    "SetMaterialTexture0",
    "SetMaterialTexture1",
    "MergeObjectMaterials",
    "AddMaterialGXItem",
    "RemoveMaterialGXItem",
]

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


class _SetMaterialTexture(LoggingOperator):

    SLOT_SUFFIX: tp.ClassVar[str]

    @classmethod
    def poll(cls, context):
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


class MergeObjectMaterials(LoggingOperator):
    """TODO: Not particularly useful for Map Pieces as hoped because of distinct baked lightmap textures."""
    bl_idname = "object.merge_object_materials"
    bl_label = "Merge Object Materials"
    bl_description = ("Look for identical FLVER materials across all selected objects and merge them into one Material "
                      "instance (e.g. for easier texture management). Old Materials are not changed or deleted.")

    @classmethod
    def poll(cls, context):
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
        found_materials = set()

        # Store all material hashes for all objects. List index will be used to replace `obj.data.materials[i]` later.
        material_hashes = {}  # type: dict[str, list[int]]

        # First, build all material hashes and create merged materials whenever a hash is found for the second time.
        for obj in flver_objects:
            obj_material_hashes = material_hashes.setdefault(obj.name, [])
            for material in obj.data.materials:
                flver_material = BlenderFLVERMaterial(material)
                material_hash = self.get_material_hash(flver_material)
                obj_material_hashes.append(material_hash)

                if material_hash in merged_materials:
                    continue  # will be replaced in second pass
                if material_hash in found_materials:
                    # Create merged material.
                    merged_materials[material_hash] = merged_material = material.copy()
                    merged_material.name = self.get_merged_material_name(flver_material)
                    self.info(f"Created merged material: {merged_material.name}")
                    continue

                # Hash found for the first time.
                found_materials.add(material_hash)

        # Now replace all appropriate materials with merged materials.
        for obj in flver_objects:
            for i, material_hash in enumerate(material_hashes[obj.name]):
                if material_hash in merged_materials:
                    # Replace material `i`.
                    obj.data.materials[i] = merged_materials[material_hash]

        self.info(f"Created {len(merged_materials)} merged materials across {len(flver_objects)} objects.")

        return {"FINISHED"}

    @staticmethod
    def get_merged_material_name(material: BlenderFLVERMaterial) -> str:
        """We strip the 'mAA_' prefixes from diffuse texture names, then add MatDef stem, <BC>, and <flags>."""
        texture_name_dict = material.get_texture_name_dict()
        texture_names = []
        for sampler_name in ("g_Diffuse", "g_Diffuse_2"):
            if sampler_name in texture_name_dict:
                texture_name = texture_name_dict[sampler_name].split(".")[0]
                if _AREA_PREFIX_RE.match(texture_name):
                    texture_name = texture_name[4:]
                texture_names.append(texture_name)
        if texture_names:
            mat_name = " + ".join(texture_names)
        else:
            mat_name = "No Diffuse"

        mat_name += f" ({Path(material.mat_def_path).stem})"

        if material.use_backface_culling:
            mat_name += " <BC>"
        if material.flags:
            mat_name += f" <{material.flags}>"

        return mat_name

    @staticmethod
    def get_material_hash(material: BlenderFLVERMaterial) -> int:
        """Hash all FLVER material properties and texture names.

        Rules:
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
    def poll(cls, context):
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
