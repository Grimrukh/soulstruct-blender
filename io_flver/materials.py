from __future__ import annotations

__all__ = [
    "DDSDict",
    "MaterialNodeCreator",
]

import typing as tp
from pathlib import Path

import bpy

if tp.TYPE_CHECKING:
    from soulstruct.base.models.flver.material import Material, Texture, MTDInfo


# TODO: Turn into import settings.
NORMAL_MAP_STRENGTH = 0.4
# TODO: Maybe water normal strength should be greater than for regular materials.
WATER_NORMAL_MAP_STRENGTH = 0.4
ROUGHNESS = 0.75


class DDSDict(dict):

    def __init__(self, operator, images: dict = None):
        self._operator = operator
        super().__init__(images)

    def __getitem__(self, texture_path: str):
        try:
            return super().__getitem__(texture_path)
        except KeyError:
            self._operator.report({"WARNING"}, f"Could not find DDS image: {texture_path}")
            return None


class MaterialNodeCreator:
    """Handles creation of various shader node trees that hold textures and simulate FromSoft materials."""

    dds_dict: DDSDict

    def __init__(self, operator, dds_images: dict[str, tp.Any] = None):
        self._operator = operator
        self.dds_dict = DDSDict(operator, dds_images)

    def create_material(
        self,
        flver_material: Material,
        material_name: str,
        use_existing=True,
        enable_alpha_hashed=True,
    ):
        """Create a Blender material that represents a single `FLVER.Material`.

        NOTE: Actual information contained in the FLVER and used for export is stored in custom properties of the
        Blender material. The node graph generated here is simply for (very helpful) visualization in Blender, and is
        NOT synchronized at all with the custom properties.

        If `use_existing=False`, a new material will be created with the FLVER's values even if a material with that
        name already exists in the Blender environment. Be wary of texture RAM usage in this case! Make sure you delete
        unneeded materials from Blender as you go.
        """

        existing_material = bpy.data.materials.get(material_name)
        if existing_material is not None:
            if use_existing:
                return existing_material
            # TODO: Should append '<i>' to duplicated name of new material...

        bl_material = bpy.data.materials.new(name=material_name)
        if enable_alpha_hashed:
            bl_material.blend_method = "HASHED"  # show alpha in viewport

        # Critical `Material` information stored in custom properties.
        bl_material["material_mtd_path"] = flver_material.mtd_path  # str
        bl_material["material_flags"] = flver_material.flags  # int
        bl_material["material_gx_index"] = flver_material.gx_index  # int
        bl_material["material_unk_x18"] = flver_material.unk_x18  # int
        bl_material["material_texture_count"] = len(flver_material.textures)  # int

        # Texture information is also stored here.
        for i, fl_tex in enumerate(flver_material.textures):
            bl_material[f"texture[{i}]_path"] = fl_tex.path  # str
            bl_material[f"texture[{i}]_texture_type"] = fl_tex.texture_type  # str
            bl_material[f"texture[{i}]_scale"] = tuple(fl_tex.scale)  # tuple (float)
            bl_material[f"texture[{i}]_unk_x10"] = fl_tex.unk_x10  # int
            bl_material[f"texture[{i}]_unk_x11"] = fl_tex.unk_x11  # bool
            bl_material[f"texture[{i}]_unk_x14"] = fl_tex.unk_x14  # float
            bl_material[f"texture[{i}]_unk_x18"] = fl_tex.unk_x18  # float
            bl_material[f"texture[{i}]_unk_x1C"] = fl_tex.unk_x1C  # float

        mtd_info = flver_material.get_mtd_info()

        bl_material.use_nodes = True
        nt = bl_material.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        output_node = nt.nodes["Material Output"]

        textures = flver_material.get_texture_dict()

        # TODO: Finesse node coordinates.

        bsdf_1 = diffuse_node_1 = bsdf_2 = diffuse_node_2 = None
        if mtd_info.diffuse or mtd_info.specular:
            bsdf_1, diffuse_node_1 = self.create_bsdf_node(textures, mtd_info, nt, is_second_slot=False)
        elif mtd_info.water:
            # Pure water shaders, such as 'A10_Water_sewer[We].mtd', do not use any BSDF nodes (bumpmap only).
            if "g_Bumpmap" not in textures:
                self._operator.report(
                    {"WARNING"},
                    f"Material '{flver_material.name}' with water shader '{flver_material.mtd_name}' does not have a "
                    f"'g_Bumpmap' texture. Blender material node tree will be incomplete."
                )
                return bl_material
            bsdf_1 = self.create_water_shader(nt, textures["g_Bumpmap"])

        vertex_colors_node = nt.nodes.new("ShaderNodeAttribute")
        vertex_colors_node.location = (-200, 430)
        vertex_colors_node.name = vertex_colors_node.attribute_name = "VertexColors"

        if mtd_info.multiple or mtd_info.alpha:
            # Use a mix shader weighted by vertex alpha.
            slot_mix_shader = nt.nodes.new("ShaderNodeMixShader")
            slot_mix_shader.location = (50, 300)
            nt.links.new(vertex_colors_node.outputs["Alpha"], slot_mix_shader.inputs["Fac"])
            nt.links.new(slot_mix_shader.outputs[0], output_node.inputs["Surface"])
        else:
            slot_mix_shader = None
            nt.links.new(bsdf_1.outputs[0], output_node.inputs["Surface"])

        if mtd_info.multiple:
            # Multi-textures shader (two slots).
            bsdf_2, diffuse_node_2 = self.create_bsdf_node(textures, mtd_info, nt, is_second_slot=True)
            nt.links.new(bsdf_1.outputs[0], slot_mix_shader.inputs[1])
            nt.links.new(bsdf_2.outputs[0], slot_mix_shader.inputs[2])
        elif mtd_info.alpha:
            # Single-texture shader (one slot). We mix with Transparent BSDF to render vertex alpha.
            # TODO: Could I not just multiply texture alpha and vertex alpha?
            transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
            transparent.location = (-200, 230)
            nt.links.new(transparent.outputs[0], slot_mix_shader.inputs[1])
            nt.links.new(bsdf_1.outputs[0], slot_mix_shader.inputs[2])
        # TODO: Not sure if I can easily support 'edge' shader alpha.
        else:
            # Single texture, no alpha. Wait to see if lightmap used below.
            pass

        if mtd_info.height:
            height_texture = flver_material.find_texture_type("g_Height")
            if height_texture is None:
                raise ValueError(
                    f"Material {material_name} has MTD {flver_material.mtd_name} but no 'g_Height' texture."
                )
            height_node = nt.nodes.new("ShaderNodeTexImage")
            height_node.location = (-550, 345)
            height_node.name = f"{height_texture.texture_type} | {Path(height_texture.path).name}"
            height_node.image = self.dds_dict[height_texture.path]
            displace_node = nt.nodes.new("ShaderNodeDisplacement")
            displace_node.location = (-250, 170)
            nt.links.new(nt.nodes["UVMap1"].outputs["Vector"], height_node.inputs["Vector"])
            nt.links.new(height_node.outputs["Color"], displace_node.inputs["Normal"])
            nt.links.new(displace_node.outputs["Displacement"], output_node.inputs["Displacement"])

        if mtd_info.lightmap:
            lightmap_texture = flver_material.find_texture_type("g_Lightmap")
            if lightmap_texture is None:
                raise ValueError(
                    f"Material {material_name} has MTD {flver_material.mtd_name} but no 'g_Lightmap' texture."
                )
            lightmap_node = nt.nodes.new("ShaderNodeTexImage")
            lightmap_node.location = (-550, 0)
            lightmap_node.name = f"{lightmap_texture.texture_type} | {Path(lightmap_texture.path).name}"
            lightmap_node.image = self.dds_dict[lightmap_texture.path]

            light_uv_attr = nt.nodes.new("ShaderNodeAttribute")
            # TODO: Would love to give the lightmap UV a more unique name, but that complicates FLVER export a bit.
            light_uv_name = "UVMap3" if mtd_info.multiple else "UVMap2"
            light_uv_attr.name = light_uv_attr.attribute_name = light_uv_name
            light_uv_attr.location = (-750, 0)
            nt.links.new(light_uv_attr.outputs["Vector"], lightmap_node.inputs["Vector"])

            # Set up overlay mix nodes between lightmap and diffuse textures.
            if diffuse_node_1:
                light_overlay_node = nt.nodes.new("ShaderNodeMixRGB")
                light_overlay_node.blend_type = "OVERLAY"
                light_overlay_node.name = "Texture 1 Lightmap Strength"
                light_overlay_node.location = (-200, 780)
                nt.links.new(diffuse_node_1.outputs["Color"], light_overlay_node.inputs[1])
                nt.links.new(lightmap_node.outputs["Color"], light_overlay_node.inputs[2])
                nt.links.new(light_overlay_node.outputs["Color"], bsdf_1.inputs["Base Color"])
            if diffuse_node_2:
                light_overlay_node = nt.nodes.new("ShaderNodeMixRGB")
                light_overlay_node.blend_type = "OVERLAY"
                light_overlay_node.name = "Texture 2 Lightmap Strength"
                light_overlay_node.location = (-200, 180)
                nt.links.new(diffuse_node_2.outputs["Color"], light_overlay_node.inputs[1])
                nt.links.new(lightmap_node.outputs["Color"], light_overlay_node.inputs[2])
                nt.links.new(light_overlay_node.outputs["Color"], bsdf_2.inputs["Base Color"])

        # TODO: Confirm "g_DetailBumpmap" has no content.

        return bl_material

    def create_bsdf_node(self, textures: dict[str, Texture], mtd_info: MTDInfo, node_tree, is_second_slot: bool):
        bsdf = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location[1] = 0 if is_second_slot else 1000
        bsdf.inputs["Roughness"].default_value = ROUGHNESS

        slot = "_2" if is_second_slot else ""
        slot_y_offset = 0 if is_second_slot else 1000

        uv_attr = node_tree.nodes.new("ShaderNodeAttribute")
        uv_attr.name = uv_attr.attribute_name = "UVMap2" if is_second_slot else "UVMap1"
        uv_attr.location = (-750, 0 + slot_y_offset)

        if mtd_info.diffuse:
            texture = textures["g_Diffuse" + slot]
            diffuse_node = node_tree.nodes.new("ShaderNodeTexImage")
            diffuse_node.location = (-550, 330 + slot_y_offset)
            diffuse_node.image = self.dds_dict[texture.path]
            diffuse_node.name = f"g_Diffuse{slot} | {Path(texture.path).name}"
            node_tree.links.new(uv_attr.outputs["Vector"], diffuse_node.inputs["Vector"])
            if not mtd_info.lightmap:  # otherwise, MixRGB node will mediate
                node_tree.links.new(diffuse_node.outputs["Color"], bsdf.inputs["Base Color"])
            node_tree.links.new(diffuse_node.outputs["Alpha"], bsdf.inputs["Alpha"])
        else:
            diffuse_node = None

        if mtd_info.specular:
            texture = textures["g_Specular" + slot]
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, 0 + slot_y_offset)
            node.image = self.dds_dict[texture.path]
            node.name = f"g_Specular{slot} | {Path(texture.path).name}"
            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], bsdf.inputs["Specular"])
        else:
            bsdf.inputs["Specular"].default_value = 0.0  # no default specularity

        if mtd_info.bumpmap:
            texture = textures["g_Bumpmap" + slot]
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.location = (-550, -330 + slot_y_offset)
            node.image = self.dds_dict[texture.path]
            node.name = f"g_Bumpmap{slot} | {Path(texture.path).name}"
            normal_map_node = node_tree.nodes.new("ShaderNodeNormalMap")
            normal_map_node.name = "NormalMap2" if is_second_slot else "NormalMap"
            normal_map_node.space = "TANGENT"
            normal_map_node.uv_map = "UVMap2" if is_second_slot else "UVMap1"
            normal_map_node.inputs["Strength"].default_value = NORMAL_MAP_STRENGTH
            normal_map_node.location = (-200, -400 + slot_y_offset)

            node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
            node_tree.links.new(node.outputs["Color"], normal_map_node.inputs["Color"])
            node_tree.links.new(normal_map_node.outputs["Normal"], bsdf.inputs["Normal"])

        # NOTE: [M] multi-texture still only uses one `g_Height` map if present.

        return bsdf, diffuse_node

    def create_water_shader(self, node_tree, bumpmap_texture):
        water_mix = node_tree.nodes.new("ShaderNodeMixShader")
        water_mix.location = (0, 1000)

        transparent = node_tree.nodes.new("ShaderNodeBsdfTransparent")
        transparent.location = (-200, 1100)
        node_tree.links.new(transparent.outputs[0], water_mix.inputs[1])

        glass = node_tree.nodes.new("ShaderNodeBsdfGlass")
        glass.location = (-200, 900)
        glass.inputs["IOR"].default_value = 1.333  # water refractive index
        node_tree.links.new(glass.outputs[0], water_mix.inputs[2])

        uv_attr = node_tree.nodes.new("ShaderNodeAttribute")
        uv_attr.name = uv_attr.attribute_name = "UVMap1"
        uv_attr.location = (-750, 1000)

        node = node_tree.nodes.new("ShaderNodeTexImage")
        node.location = (-550, 670)
        node.image = self.dds_dict[bumpmap_texture.path]
        node.name = f"g_Bumpmap | {Path(bumpmap_texture.path).name}"
        normal_map_node = node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map_node.name = "NormalMap"
        normal_map_node.space = "TANGENT"
        normal_map_node.uv_map = "UVMap1"
        normal_map_node.inputs["Strength"].default_value = WATER_NORMAL_MAP_STRENGTH
        normal_map_node.location = (-200, 600)

        node_tree.links.new(uv_attr.outputs["Vector"], node.inputs["Vector"])
        node_tree.links.new(node.outputs["Color"], normal_map_node.inputs["Color"])
        node_tree.links.new(normal_map_node.outputs["Normal"], glass.inputs["Normal"])

        return water_mix
