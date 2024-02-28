from __future__ import annotations

__all__ = [
    "get_submesh_blender_material",
]

import typing as tp

import bpy

from soulstruct.base.models.flver.material import Material
from soulstruct.base.models.flver.submesh import Submesh
from soulstruct.utilities.maths import Vector2

from io_soulstruct.utilities.operators import LoggingOperator
from .material_info import *

# Node input for specular strength is called "Specular IOR Level" in Blender 4.X, but just "Specular" prior to that.
if bpy.app.version[0] == 4:
    PRINCIPLED_SPEC_INPUT = "Specular IOR Level"
else:
    PRINCIPLED_SPEC_INPUT = "Specular"


def get_submesh_blender_material(
    operator: LoggingOperator,
    material: Material,
    texture_stem_dict: dict[str, str],
    material_name: str,
    material_info: BaseMaterialShaderInfo,
    submesh: Submesh,
    vertex_color_count: int,
    blend_mode="HASHED",
    warn_missing_textures=True,
) -> bpy.types.Material:
    """Create a new material in the current Blender scene from a FLVER material.

    Will use material texture stems to search for PNG or DDS images in the Blender image data. If no image is found,
    the texture will be left unassigned in the material.
    """

    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    if blend_mode:
        bl_material.blend_method = blend_mode

    # Critical `Material` information stored in custom properties.
    bl_material["Flags"] = material.flags  # int
    bl_material["Mat Def Path"] = material.mat_def_path  # str
    bl_material["Unk x18"] = material.unk_x18  # int
    # NOTE: Texture path prefixes not stored, as they aren't actually needed in the TPFBHDs.

    # Set additional real and custom properties from FLVER submesh.
    bl_material["Is Bind Pose"] = submesh.is_bind_pose
    # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
    bl_material["Default Bone Index"] = submesh.default_bone_index
    # Currently, main face set is simply copied to all additional face sets on export.
    bl_material["Face Set Count"] = len(submesh.face_sets)
    bl_material.use_backface_culling = submesh.use_backface_culling

    # Store GX items as custom properties 'array', except the final dummy array.
    for i, gx_item in enumerate(material.gx_items):
        if gx_item.is_dummy:
            continue  # ignore dummy items
        try:
            bl_material[f"GXItem[{i}] Category"] = gx_item.category.decode()
        except UnicodeDecodeError:
            operator.warning(f"Could not decode GXItem {i} category: {gx_item.category}. Storing empty string.")
            bl_material[f"GXItem[{i}] Category"] = ""
        bl_material[f"GXItem[{i}] Index"] = gx_item.index
        bl_material[f"GXItem[{i}] Data"] = repr(gx_item.data)

    # Try to build shader nodetree.
    builder = NodeTreeBuilder(operator, bl_material, warn_missing_textures)
    builder.build(material_info, texture_stem_dict, vertex_color_count)

    return bl_material


class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials."""

    operator: LoggingOperator
    material: bpy.types.Material
    tree: bpy.types.NodeTree
    output: bpy.types.Node
    warn_missing_textures: bool

    vertex_colors_nodes: list[bpy.types.Node]
    uv_nodes: dict[str, bpy.types.Node]
    tex_image_nodes: dict[str, bpy.types.Node]

    # X coordinates of node type columns.
    VERTEX_COLORS_X = -950
    UV_X = -950
    SCALE_X = -750
    TEX_X = -550
    OVERLAY_X = -250  # includes Normal Map node for 'g_Bumpmap'
    BSDF_X = -50
    MIX_X, MIX_Y = 100, 300  # only one (max)

    def __init__(self, operator: LoggingOperator, material: bpy.types.Material, warn_missing_textures: bool):
        self.operator = operator
        self.material = material
        self.tree = material.node_tree
        self.output = self.tree.nodes["Material Output"]
        self.warn_missing_textures = warn_missing_textures

        # Auto-decremented Y coordinates for each node type (so newer nodes are further down).
        self.uv_y = 1000
        self.tex_y = 1000
        self.bsdf_y = 1000

    def build(
        self,
        material_info: BaseMaterialShaderInfo,
        texture_stem_dict: dict[str, str],
        vertex_color_count: int,
    ):

        # Wipe default nodes (except output).
        self.tree.nodes.remove(self.tree.nodes["Principled BSDF"])
        self.tree.links.clear()

        # Build vertex color, UV, and texture nodes.
        self.vertex_colors_nodes = [self.add_vertex_colors_node(i) for i in range(vertex_color_count)]
        try:
            self.build_shader_uv_texture_nodes(material_info, texture_stem_dict)
        except KeyError as ex:
            self.operator.warning(
                f"Could not build UV coordinate nodes for material with shader {material_info.shader_stem}. Error: {ex}"
            )
            return  # don't bother trying to build full shader below

        # Build out the rest of the nodetree, which is game-dependent.
        if isinstance(material_info, DS1MaterialShaderInfo):
            self.build_ds1_shader(material_info)
        elif isinstance(material_info, BBMaterialShaderInfo):
            self.build_bb_shader(material_info)
        elif isinstance(material_info, ERMaterialShaderInfo):
            try:
                self.build_er_shader(material_info)
            except Exception as ex:
                self.operator.warning(
                    f"Cannot yet build shader for Elden Ring shader: {material_info.shader_stem}. Error: {ex}"
                )
        else:
            self.operator.warning(
                f"Cannot yet build shader for unknown shader info class '{material_info.__class__.__name__}'."
            )

    def build_shader_uv_texture_nodes(
        self,
        material_info: BaseMaterialShaderInfo,
        texture_stem_dict: dict[str, str],
    ):
        """Build UV and texture nodes. Shared across all games."""
        self.uv_nodes = {}
        self.tex_image_nodes = {}  # type: dict[str, bpy.types.Node]

        missing_textures = list(material_info.sampler_types)
        for texture_type, texture_stem in texture_stem_dict.items():
            if texture_type not in material_info.sampler_types:
                self.operator.warning(
                    f"Texture type '{texture_type}' does not seem to be supported by shader "
                    f"'{material_info.shader_stem}'. Creating FLVER material texture node anyway with UV index 1.",
                )
                uv_index = 1
            elif texture_type not in missing_textures:
                self.operator.warning(
                    f"Texture type '{texture_type}' was given multiple times in FLVER material, which is invalid. "
                    f"Please repair this corrupt FLVER file. Ignoring this texture.",
                )
                continue
            else:
                # Found expected sampler type for the first time.
                missing_textures.remove(texture_type)
                try:
                    uv_index = material_info.sampler_type_uv_indices[texture_type]
                except KeyError:
                    self.operator.warning(
                        f"Sampler type '{texture_type}' is missing a UV index in the material shader info. "
                        f"Creating FLVER material texture node anyway (with no UV input).",
                    )
                    uv_index = None

            if not texture_stem:
                # Empty texture in FLVER (e.g. 'g_DetailBumpmap' in every single DS1 FLVER).
                tex_image_node = self.add_tex_image_node(texture_type, None)
                self.tex_image_nodes[texture_type] = tex_image_node
                continue

            # Try to find texture in Blender image data as a PNG (preferred) or DDS.
            # TODO: 'DetailBump_01_n' texture seems to be missing from characters' `g_DetailBumpmap` slot. Handle?
            #  I think it's in some common texture bunch, potentially?

            for image_name in (f"{texture_stem}", f"{texture_stem}.png", f"{texture_stem}.dds"):
                if image_name in bpy.data.images:
                    bl_image = bpy.data.images[image_name]
                    break
            else:
                # Create empty Blender image.
                bl_image = bpy.data.images.new(name=texture_stem, width=1, height=1, alpha=True)
                bl_image.pixels = [1.0, 0.0, 1.0, 1.0]  # magenta
                self.operator.warning(
                    f"Could not find texture '{texture_stem}' in Blender image data. "
                    f"Created 1x1 magenta texture for node."
                )

            tex_image_node = self.add_tex_image_node(texture_type, bl_image)
            self.tex_image_nodes[texture_type] = tex_image_node

            if uv_index is not None:
                # Connect to appropriate UV node, creating it if necessary.
                uv_map_name = f"UVMap{uv_index}"
                uv_node = self.uv_nodes.setdefault(uv_map_name, self.add_uv_node(uv_map_name))

                if isinstance(material_info, ERMaterialShaderInfo):
                    uv_scale = material_info.sampler_uv_scales[texture_type]
                    uv_scale_node = self.add_tex_scale_node(uv_scale, tex_image_node.location.y)
                    self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
                    self.link(uv_scale_node.outputs["Vector"], tex_image_node.inputs["Vector"])
                else:
                    self.link(uv_node.outputs["Vector"], tex_image_node.inputs["Vector"])

    def build_ds1_shader(self, material_info: DS1MaterialShaderInfo):
        """Attempt to craft a faithful shader for a DS1 material."""
        bsdf_nodes = [None, None]  # type: list[bpy.types.Node | None]

        if material_info.is_water:
            # Special simplified shader. Uses 'g_Bumpmap' only.
            water_mix = self.new("ShaderNodeMixShader", (self.MIX_X, self.MIX_Y))
            transparent = self.new("ShaderNodeBsdfTransparent", (self.BSDF_X, self.MIX_Y))
            glass = self.new("ShaderNodeBsdfGlass", (self.BSDF_X, 1000), input_defaults={"IOR": 1.333})
            self.link(transparent.outputs[0], water_mix.inputs[1])
            self.link(glass.outputs[0], water_mix.inputs[2])

            bumpmap_node = self.tex_image_nodes["g_Bumpmap"]
            normal_map_node = self.add_normal_map_node("UVMap0", bumpmap_node.location[1])

            self.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
            self.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], water_mix.inputs["Fac"])
            return

        # TODO: Sketch for snow shader:
        #  - Create a Diffuse BSDF shader with HSV (0.75, 0.3, 1.0) (blue tint).
        #  - Mix g_Bumpmap_2 and (if present) g_Bumpmap_3 with Mix RGB.
        #  - Plug into Normal Map using UVMap0 (always UVMap0, regardless of what MTD says - though this is handled).
        #  - Create a Mix Shader for the standard textures and new Diffuse snow BSDF. Plug into material output.
        #  - Use Math node to raise VertexColors alpha to exponent 10 and use that as Fac of the Mix Shader.
        #     - This shows roughly where the snow will be created without completely obscuring the underlying texture.
        #  - If a lightmap is present, instead mix that mix shader with it!

        # Standard shader: one or two Principled BSDFs mixed 50/50, or one Principled BSDF mixed with a Transparent BSDF
        # for alpha-supporting shaders (includes edge shaders currently).
        bsdf_nodes[0] = self.add_principled_bsdf_node("Texture Slot 0")
        if material_info.slot_count > 1:
            if material_info.slot_count > 2:
                self.operator.warning("Cannot yet set up DS1 Blender shader for more than two texture groups.")
            bsdf_nodes[1] = self.add_principled_bsdf_node("Texture Slot 1")
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], mix_node.inputs["Fac"])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        elif material_info.alpha or material_info.edge:
            # Mix main Principled BSDF with a Transparent BSDF using vertex alpha.
            # TODO: Assumes single BSDF; will not render second texture slot at all. Confirm 'M' shaders never use Alp.
            transparent_node = self.new("ShaderNodeBsdfTransparent", location=(self.BSDF_X, self.bsdf_y))
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(transparent_node.outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[2])  # more vertex alpha -> more opacity
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], mix_node.inputs["Fac"])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        else:
            self.link_to_output_surface(bsdf_nodes[0].outputs["BSDF"])

        if "g_Lightmap" in self.tex_image_nodes:
            lightmap_node = self.tex_image_nodes["g_Lightmap"]
            for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
                if texture_type not in self.tex_image_nodes:
                    continue
                bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
                if bsdf_node is None:
                    continue  # TODO: bad state
                tex_image_node = self.tex_image_nodes[texture_type]
                overlay_node_y = tex_image_node.location[1]
                overlay_node = self.new(
                    "ShaderNodeMixRGB", location=(self.OVERLAY_X, overlay_node_y), blend_type="OVERLAY"
                )
                self.link(tex_image_node.outputs["Color"], overlay_node.inputs["Color1"])
                self.link(lightmap_node.outputs["Color"], overlay_node.inputs["Color2"])  # order is important!

                if texture_type.startswith("g_Diffuse"):
                    bsdf_input = "Base Color"
                else:  # g_Specular
                    bsdf_input = PRINCIPLED_SPEC_INPUT

                self.link(overlay_node.outputs["Color"], bsdf_node.inputs[bsdf_input])
                if texture_type.startswith("g_Diffuse"):
                    # Plug diffuse alpha into BSDF alpha.
                    self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
        else:
            # Plug diffuse and specular textures directly into Principled BSDF.
            for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
                if texture_type not in self.tex_image_nodes:
                    continue
                bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
                if bsdf_node is None:
                    continue  # TODO: bad state
                tex_image_node = self.tex_image_nodes[texture_type]
                if texture_type.startswith("g_Diffuse"):
                    self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                    self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
                else:  # g_Specular[_2]
                    self.link(tex_image_node.outputs["Color"], bsdf_node.inputs[PRINCIPLED_SPEC_INPUT])

        if "g_Height" in self.tex_image_nodes:
            # 'g_Height' is an actual height map (not normals, like 'g_Bumpmap').
            height_node = self.tex_image_nodes["g_Height"]
            # NOTE: In my observation so far, this always uses UVMap0 (i.e. never the second texture in a two-slot mat).
            self.link(self.uv_nodes["UVMap0"].outputs["Vector"], height_node.inputs["Vector"])
            self.link_to_output_displacement(height_node.outputs["Color"])

        for texture_type, bsdf_node in zip(("g_Bumpmap", "g_Bumpmap_2"), bsdf_nodes):
            if texture_type not in self.tex_image_nodes or texture_type not in material_info.sampler_types:
                continue
            if bsdf_node is None:
                continue  # TODO: bad state
            # Create normal map node.
            bumpmap_node = self.tex_image_nodes[texture_type]
            uv_index = material_info.sampler_type_uv_indices[texture_type]
            uv_map_name = f"UVMap{uv_index}"
            normal_map_node = self.add_normal_map_node(uv_map_name, bumpmap_node.location[1])
            self.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
            self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    def build_bb_shader(self, material_info: BBMaterialShaderInfo):
        """Attempt to craft a faithful shader for a Bloodborne material.

        TODO:
            - Plug in g_DisplacementTexture.
            - Fix search for specific map textures.
            - Use 'g_BlendMaskTexture' as mix shader Fac instead of vertex color.
        """
        bsdf_nodes = [None, None]  # type: list[bpy.types.Node | None]

        if material_info.is_water:  # TODO: check for BB
            # Special simplified shader. Uses 'g_Bumpmap' only.
            water_mix = self.new("ShaderNodeMixShader", (self.MIX_X, self.MIX_Y))
            transparent = self.new("ShaderNodeBsdfTransparent", (self.BSDF_X, self.MIX_Y))
            glass = self.new("ShaderNodeBsdfGlass", (self.BSDF_X, 1000), input_defaults={"IOR": 1.333})
            self.link(transparent.outputs[0], water_mix.inputs[1])
            self.link(glass.outputs[0], water_mix.inputs[2])

            bumpmap_node = self.tex_image_nodes["g_BumpmapTexture"]
            normal_map_node = self.add_normal_map_node("UVMap0", bumpmap_node.location[1])

            self.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
            self.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], water_mix.inputs["Fac"])
            return

        # Standard shader: one or two Principled BSDFs mixed 50/50, or one Principled BSDF mixed with a Transparent BSDF
        # for alpha-supporting shaders (includes edge shaders currently).
        bsdf_nodes[0] = self.add_principled_bsdf_node("Texture Slot 0")
        if material_info.slot_count > 1:
            if material_info.slot_count > 2:
                self.operator.warning("Cannot yet set up DS1 Blender shader for more than two texture groups.")
            bsdf_nodes[1] = self.add_principled_bsdf_node("Texture Slot 1")
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
            if "g_BlendMaskTexture" in self.tex_image_nodes:
                blend_mask_node = self.tex_image_nodes["g_BlendMaskTexture"]
                self.link(blend_mask_node.outputs["Color"], mix_node.inputs["Fac"])
            else:
                # NOTE: May not be correct; unsure if vertex colors are used if g_BlendMaskTexture is not present.
                self.link(self.vertex_colors_nodes[0].outputs["Alpha"], mix_node.inputs["Fac"])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        elif material_info.alpha or material_info.edge:
            # Mix main Principled BSDF with a Transparent BSDF using vertex alpha.
            # TODO: Assumes single BSDF; will not render second texture slot at all. Confirm 'M' shaders never use Alp.
            transparent_node = self.new("ShaderNodeBsdfTransparent", location=(self.BSDF_X, self.bsdf_y))
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(transparent_node.outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[2])  # more vertex alpha -> more opacity
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], mix_node.inputs["Fac"])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        else:
            self.link_to_output_surface(bsdf_nodes[0].outputs["BSDF"])

        if "g_LightmapTexture" in self.tex_image_nodes:
            lightmap_node = self.tex_image_nodes["g_LightmapTexture"]
            for texture_type in (
                "g_DiffuseTexture", "g_SpecularTexture", "g_ShininessTexture",
                "g_DiffuseTexture2", "g_SpecularTexture2", "g_ShininessTexture2",
            ):
                if texture_type not in self.tex_image_nodes:
                    continue
                bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
                if bsdf_node is None:
                    continue  # TODO: bad state
                tex_image_node = self.tex_image_nodes[texture_type]
                overlay_node_y = tex_image_node.location[1]
                overlay_node = self.new(
                    "ShaderNodeMixRGB", location=(self.OVERLAY_X, overlay_node_y), blend_type="OVERLAY"
                )
                self.link(tex_image_node.outputs["Color"], overlay_node.inputs["Color1"])
                self.link(lightmap_node.outputs["Color"], overlay_node.inputs["Color2"])  # order is important!

                if texture_type.startswith("g_DiffuseTexture"):
                    self.link(overlay_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                    self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
                elif texture_type.startswith("g_ShininessTexture"):
                    self.link(overlay_node.outputs["Color"], bsdf_node.inputs["Sheen"])
                else:  # g_SpecularTexture[2]
                    self.link(overlay_node.outputs["Color"], bsdf_node.inputs[PRINCIPLED_SPEC_INPUT])

        else:
            # Plug diffuse and specular textures directly into Principled BSDF.
            for texture_type in (
                "g_DiffuseTexture", "g_SpecularTexture", "g_ShininessTexture",
                "g_DiffuseTexture2", "g_SpecularTexture2", "g_ShininessTexture2",
            ):
                if texture_type not in self.tex_image_nodes:
                    continue
                bsdf_node = bsdf_nodes[1] if texture_type.endswith("2") else bsdf_nodes[0]
                if bsdf_node is None:
                    continue  # TODO: bad state
                tex_image_node = self.tex_image_nodes[texture_type]
                if texture_type.startswith("g_DiffuseTexture"):
                    self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                    self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
                elif texture_type.startswith("g_ShininessTexture"):
                    self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Sheen"])
                else:  # g_SpecularTexture[2]
                    self.link(tex_image_node.outputs["Color"], bsdf_node.inputs[PRINCIPLED_SPEC_INPUT])

        # TODO: 'g_DisplacementTexture' in BB
        # if "g_Height" in self.tex_image_nodes:
        #     # 'g_Height' is an actual height map (not normals, like 'g_Bumpmap').
        #     height_node = self.tex_image_nodes["g_Height"]
        #     # NOTE: In my observation so far, this always uses UVMap0 (i.e. never the second texture in two-slot mat).
        #     self.link(self.uv_nodes["UVMap0"].outputs["Vector"], height_node.inputs["Vector"])
        #     self.link_to_output_displacement(height_node.outputs["Color"])

        for texture_type, bsdf_node in zip(("g_BumpmapTexture", "g_BumpmapTexture2"), bsdf_nodes):
            if texture_type not in self.tex_image_nodes or texture_type not in material_info.sampler_types:
                continue
            if bsdf_node is None:
                continue  # TODO: bad state
            # Create normal map node.
            bumpmap_node = self.tex_image_nodes[texture_type]
            uv_index = material_info.sampler_type_uv_indices[texture_type]
            uv_map_name = f"UVMap{uv_index}"
            normal_map_node = self.add_normal_map_node(uv_map_name, bumpmap_node.location[1])
            self.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
            self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    def build_er_shader(self, material_info: ERMaterialShaderInfo):
        """Attempt to craft a faithful shader for an Elden Ring material."""

        bsdf_nodes = [None, None, None]  # type: list[bpy.types.Node | None]
        bsdf_nodes[0] = self.add_principled_bsdf_node("Texture Slot 0")

        # TODO: How to use Vertex Colors? Maybe more shader-dependent.

        if material_info.slot_count > 1:
            bsdf_nodes[1] = self.add_principled_bsdf_node("Texture Slot 1")
        if material_info.slot_count > 2:
            bsdf_nodes[2] = self.add_principled_bsdf_node("Texture Slot 2")
        if material_info.slot_count > 3:
            self.operator.warning("Cannot yet set up Blender shader for more than two texture groups.")

        if material_info.slot_count == 3:
            # Mix second and third BSDF nodes.
            mix_2_3_node = self.new("ShaderNodeMixShader", location=(self.MIX_X - 100, self.MIX_Y - 100))
            self.link(bsdf_nodes[1].outputs["BSDF"], mix_2_3_node.inputs[1])
            self.link(bsdf_nodes[2].outputs["BSDF"], mix_2_3_node.inputs[2])
            # Mix first BSDF node with mix of second and third.
            mix_1_2_3_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_1_2_3_node.inputs[1])
            self.link(mix_2_3_node.outputs["Shader"], mix_1_2_3_node.inputs[2])
            self.link_to_output_surface(mix_1_2_3_node.outputs["Shader"])
        elif material_info.slot_count == 2:
            # Just mix first and second BSDF nodes.
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        else:
            self.link_to_output_surface(bsdf_nodes[0].outputs["BSDF"])

        for sampler_type, tex_image_node in self.tex_image_nodes.items():
            if tex_image_node.image is None:
                tex_image_node.hide = True
                continue  # no shader setup
            uv_index = material_info.sampler_type_uv_indices[sampler_type]
            group_index = material_info.sampler_uv_groups[sampler_type]
            if group_index == 1:
                bsdf_node = bsdf_nodes[0]
            elif group_index == 2:
                bsdf_node = bsdf_nodes[1]
            elif group_index == 3:
                bsdf_node = bsdf_nodes[2]
            else:
                continue  # no shader setup
            if not bsdf_node:
                continue  # not enough slots detected

            if "AlbedoMap" in sampler_type:
                self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            if "MetallicMap" in sampler_type:
                self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Metallic"])
            if "NormalMap" in sampler_type:
                normal_map_node = self.add_normal_map_node(f"UVMap{uv_index}", tex_image_node.location[1])
                self.link(tex_image_node.outputs["Color"], normal_map_node.inputs["Color"])
                self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    # region Builder Methods

    def new(
        self, node_type: str, location: tuple[int, int] = None, /, input_defaults: dict[str, tp.Any] = None, **kwargs
    ) -> bpy.types.Node:
        node = self.tree.nodes.new(node_type)
        if location is not None:
            node.location = location
        for k, v in kwargs.items():
            setattr(node, k, v)
        if input_defaults:
            for k, v in input_defaults.items():
                node.inputs[k].default_value = v
        return node

    def link(self, node_output, node_input) -> bpy.types.NodeLink:
        return self.tree.links.new(node_output, node_input)

    def link_to_output_surface(self, node_output) -> bpy.types.NodeLink:
        return self.link(node_output, self.output.inputs["Surface"])

    def link_to_output_volume(self, node_output) -> bpy.types.NodeLink:
        return self.link(node_output, self.output.inputs["Volume"])

    def link_to_output_displacement(self, node_output) -> bpy.types.NodeLink:
        return self.link(node_output, self.output.inputs["Displacement"])

    def add_vertex_colors_node(self, index: int) -> bpy.types.Node:
        return self.new(
            "ShaderNodeAttribute",
            location=(self.OVERLAY_X, 1200 + index * 200),
            name=f"VertexColors{index}",
            attribute_name=f"VertexColors{index}",
        )

    def add_uv_node(self, uv_map_name: str):
        """Create an attribute node for the given UV layer name."""
        node = self.new(
            "ShaderNodeAttribute",
            location=(self.UV_X, self.uv_y),
            name=uv_map_name,
            attribute_name=uv_map_name,
            label=uv_map_name,
        )
        self.uv_y -= 1000
        return node

    def add_tex_scale_node(self, scale: Vector2, node_y: float):
        node = self.new(
            "ShaderNodeVectorMath",
            location=(self.SCALE_X, node_y),
            operation="MULTIPLY",
            label="UV Scale",
        )
        node.inputs[1].default_value = [scale.x, scale.y, 1.0]
        return node

    def add_tex_image_node(self, texture_type: str, image: bpy.types.Image | None):
        node = self.new(
            "ShaderNodeTexImage",
            location=(self.TEX_X, self.tex_y),
            image=image,
            name=texture_type,
            label=texture_type,
        )
        self.tex_y -= 330
        return node

    def add_principled_bsdf_node(self, bsdf_name: str):
        node = self.new(
            "ShaderNodeBsdfPrincipled",
            location=(self.BSDF_X, self.bsdf_y),
            name=bsdf_name,
            input_defaults={"Roughness": 0.75},
        )
        self.bsdf_y -= 1000
        return node

    def add_normal_map_node(self, uv_map_name: str, location_y: float):
        return self.new(
            "ShaderNodeNormalMap",
            location=(self.OVERLAY_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": 0.4},
        )

    # endregion
