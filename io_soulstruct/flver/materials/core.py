from __future__ import annotations

__all__ = [
    "MaterialCreationError",
    "create_submesh_blender_material",
]

import typing as tp

import bpy

from soulstruct.base.models.flver.material import Material
from soulstruct.base.models.flver.submesh import Submesh
from soulstruct.utilities.maths import Vector2

from io_soulstruct.utilities.operators import LoggingOperator
from .material_info import *

# Main node input for specular strength is called "Specular IOR Level" in Blender 4.X, but "Specular" prior to that.
if bpy.app.version[0] == 4:
    PRINCIPLED_SPECULAR_INPUT = "Specular IOR Level"
    PRINCIPLED_SHEEN_INPUT = "Sheen Weight"
    PRINCIPLED_TRANSMISSION_INPUT = "Transmission Weight"
else:
    PRINCIPLED_SPECULAR_INPUT = "Specular"
    PRINCIPLED_SHEEN_INPUT = "Sheen"
    PRINCIPLED_TRANSMISSION_INPUT = "Transmission"


class MaterialCreationError(Exception):
    """Error raised during material shader creation. Generally non-fatal, as the critical texture nodes required for
    export are typically easy to create. This just means a more faithful shader couldn't be built."""


def create_submesh_blender_material(
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
    """Create a new Blender material from a FLVER material.

    Will use material texture stems to search for PNG or DDS images in the Blender image data. If no image is found,
    the texture will be left unassigned in the material.

    Attempts to build a Blender node tree for the material. The only critical information stored in the node tree is the
    sampler names (node labels) and image names (image node `Image` names) of the `ShaderNodeTexImage` nodes created.
    We attempt to connect those textures to UV maps and BSDF nodes, but this is just an attempt to replicate the game
    engine's shaders, and is not needed for FLVER export. (NOTE: Elden Ring tends to store texture paths in MATBIN files
    rather than in the FLVER materials, so even the texture names may not be used on export.)
    """

    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    if blend_mode:
        if material_info.edge:
            # Always uses "CLIP".
            bl_material.blend_method = "CLIP"
            bl_material.alpha_threshold = 0.5
        else:
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
    # TODO: Currently, main face set is simply copied to all additional face sets on export. This is fine for early
    #  games, but probably not for, say, Elden Ring map pieces.
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

    # Maps vertex color layer names (e.g. 'VertexColor0') to Nodes. (Remember that these are actually LOOP colors.)
    vertex_colors_nodes: list[bpy.types.Node]
    # Maps UV global layer names (e.g. 'UVTexture0') to Nodes.
    uv_nodes: dict[str, bpy.types.Node]
    # Maps common, non-game-specific sampler type (e.g. 'ALBEDO_0') to Nodes.
    tex_image_nodes: dict[str, bpy.types.Node]

    # X coordinates of node type columns.
    VERTEX_COLORS_X = -950
    UV_X = -950
    SCALE_X = -750
    TEX_X = -550
    POST_TEX_X = -250  # overlay, split, math, etc.
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
        # Note that the texture nodes (specifically, their sampler labels and `Image` names) are the only information in
        # the node tree critical for FLVER export.
        self.vertex_colors_nodes = [self.add_vertex_colors_node(i) for i in range(vertex_color_count)]
        try:
            self.build_shader_uv_texture_nodes(material_info, texture_stem_dict)
        except KeyError as ex:
            self.operator.warning(
                f"Could not build UV coordinate nodes for material with shader {material_info.shader_stem}. Error: {ex}"
            )
            return  # don't bother trying to build full shader below

        try:
            special_built = self.build_common_special_shader(material_info)
        except MaterialCreationError as ex:
            self.operator.warning(
                f"Error building special shader for material with shader {material_info.shader_stem}. Error: {ex}"
            )
            return
        if special_built:
            return

        # Build game-dependent shader.
        try:
            if isinstance(material_info, ERMaterialShaderInfo):
                self.build_er_shader(material_info)
            else:
                self.build_common_generic_shader(material_info)
        except MaterialCreationError as ex:
            self.operator.warning(
                f"Error building shader for material with shader {material_info.shader_stem}. Error: {ex}"
            )

    def build_shader_uv_texture_nodes(
        self,
        material_info: BaseMaterialShaderInfo,
        flver_texture_stems: dict[str, str],
    ):
        """Build UV and texture nodes. Shared across all games."""
        self.uv_nodes = {}
        self.tex_image_nodes = {}  # type: dict[str, bpy.types.Node]

        missing_textures = list(material_info.sampler_names)
        sampler_to_common_names = material_info.SAMPLER_NAMES.as_reverse_dict()

        for sampler_name, texture_stem in flver_texture_stems.items():
            if sampler_name not in material_info.sampler_names:
                self.operator.warning(
                    f"Sampler '{sampler_name}' does not seem to be supported by shader "
                    f"'{material_info.shader_stem}'. Texture node created, but with no UV layer input.",
                )
                uv_layer_name = None
            elif sampler_name not in missing_textures:
                self.operator.warning(
                    f"Texture for sampler '{sampler_name}' was given multiple times in FLVER material, which is "
                    f"invalid. Please repair this corrupt FLVER file. Ignoring this texture.",
                )
                continue
            else:
                # Found expected sampler type for the first time.
                missing_textures.remove(sampler_name)
                try:
                    uv_layer_name = material_info.sampler_name_uv_layers[sampler_name].name
                except KeyError:
                    self.operator.warning(
                        f"Sampler type '{sampler_name}' is missing a UV index in the material shader info. "
                        f"Texture node created, but with no UV layer input.",
                    )
                    uv_layer_name = None

            # We use the common name for the node if possible, but the actual texture name for the image.
            # The exporter will prefer the name. This makes it easier to port FLVERs to other games with different
            # sampler names, while still recording the original sampler name for posterity.
            node_name = sampler_to_common_names.get(sampler_name, sampler_name)
            node_label = sampler_name

            if not texture_stem:
                # Empty texture in FLVER (e.g. 'g_DetailBumpmap' in every single DS1 FLVER).
                tex_image_node = self.add_tex_image_node(node_name, image=None, label=node_label)
                self.tex_image_nodes[node_name] = tex_image_node
                continue

            # Try to find texture in Blender image data as a PNG (preferred) or DDS.
            # TODO: 'DetailBump_01_n' texture seems to be missing from characters' `g_DetailBumpmap` slot. Handle?
            #  I think it's in some common texture bunch, potentially?

            # Search for Blender image with no extension, PNG, or DDS, in that order of preference.
            for image_name in (f"{texture_stem}", f"{texture_stem}.png", f"{texture_stem}.dds"):
                if image_name in bpy.data.images:
                    bl_image = bpy.data.images[image_name]
                    break
            else:
                # Blender image not found. Create empty Blender image.
                bl_image = bpy.data.images.new(name=texture_stem, width=1, height=1, alpha=True)
                bl_image.pixels = [1.0, 0.0, 1.0, 1.0]  # magenta
                self.operator.warning(
                    f"Could not find texture '{texture_stem}' (no extension, PNG, or DDS) in Blender image data. "
                    f"Created 1x1 magenta texture for node."
                )

            tex_image_node = self.add_tex_image_node(node_name, image=bl_image, label=node_label)
            self.tex_image_nodes[node_name] = tex_image_node

            if uv_layer_name is not None:
                # Connect to appropriate UV node, creating it if necessary.
                if uv_layer_name in self.uv_nodes:
                    uv_node = self.uv_nodes[uv_layer_name]
                else:
                    uv_node = self.uv_nodes[uv_layer_name] = self.add_uv_node(uv_layer_name)
                if isinstance(material_info, ERMaterialShaderInfo):
                    # Elden Ring materials define extra scaling for certain texture groups. We replicate it to produce
                    # a more faithful shader in Blender. None of this is exported (still just texture names!).
                    uv_scale = material_info.sampler_uv_scales[sampler_name]
                    uv_scale_node = self.add_tex_scale_node(uv_scale, tex_image_node.location.y)
                    self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
                    self.link(uv_scale_node.outputs["Vector"], tex_image_node.inputs["Vector"])
                else:
                    self.link(uv_node.outputs["Vector"], tex_image_node.inputs["Vector"])

    def build_common_special_shader(self, material_info: BaseMaterialShaderInfo) -> bool:
        """Check for common special shader types, like water, that are present across games.

        Returns `True` if a special shader was found and handled.
        """
        if material_info.is_water:
            # Special simplified shader. Uses 'g_Bumpmap' only.
            water_mix = self.new("ShaderNodeMixShader", (self.MIX_X, self.MIX_Y))
            transparent = self.new("ShaderNodeBsdfTransparent", (self.BSDF_X, self.MIX_Y))
            glass = self.new("ShaderNodeBsdfGlass", (self.BSDF_X, 1000), input_defaults={"IOR": 1.333})
            self.link(transparent.outputs[0], water_mix.inputs[1])
            self.link(glass.outputs[0], water_mix.inputs[2])

            bumpmap_node = self.tex_image_nodes["NORMAL_0"]
            try:
                uv_texture_0 = material_info.UVLayer["UVTexture0"].name
            except KeyError:
                raise MaterialCreationError(
                    "This game material info does not define 'UVTexture0' layer, which is required for water shader."
                )

            normal_map_node = self.add_normal_map_node(uv_texture_0, bumpmap_node.location[1])
            self.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
            self.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], water_mix.inputs["Fac"])
            return True

        # TODO: Sketch for snow shader:
        #  - Create a Diffuse BSDF shader with HSV (0.75, 0.3, 1.0) (blue tint).
        #  - Mix g_Bumpmap_2 and (if present) g_Bumpmap_3 with Mix RGB.
        #  - Plug into Normal Map using UVTexture0 (regardless of what MTD says - though this is handled).
        #  - Create a Mix Shader for the standard textures and new Diffuse snow BSDF. Plug into material output.
        #  - Use Math node to raise VertexColors alpha to exponent 10 and use that as Fac of the Mix Shader.
        #     - This shows roughly where the snow will be created without completely obscuring the underlying texture.
        #  - If a lightmap is present, instead mix that mix shader with it!

        return False

    def build_common_generic_shader(self, material_info: BaseMaterialShaderInfo):
        """Build cross-game, standard types of shaders using common sampler names like 'ALBEDO_0'.

        Returns `True` if a generic shader was found and handled.

        TODO: Biggest improvements here would be adjusting overall specularity for Wood, Stone, etc.
        """
        bsdf_nodes = [None, None]  # type: list[bpy.types.Node | None]

        # Standard shader: one or two Principled BSDFs mixed 50/50, or one Principled BSDF mixed with a Transparent BSDF
        # for alpha-supporting shaders (includes edge shaders currently).
        bsdf_nodes[0] = self.add_principled_bsdf_node("Texture Slot 0")
        if material_info.slot_count > 1:
            if material_info.slot_count > 2:
                # TODO: Support 3+ texture groups (e.g. Elden Ring).
                self.operator.warning(
                    "Cannot yet set up Blender shader for more than two texture groups. Later textures not linked."
                )
            bsdf_nodes[1] = self.add_principled_bsdf_node("Texture Slot 1")
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
            if material_info.SAMPLER_NAMES.BLEND_01:
                if "BLEND_01" in self.tex_image_nodes:
                    blend_node = self.tex_image_nodes["BLEND_01"]
                    self.link(blend_node.outputs["Color"], mix_node.inputs["Fac"])
                else:
                    self.operator.warning(
                        "This game material info defines BLEND_01, but no BLEND_01 texture was found. Cannot weight "
                        "textures in shader; using 0.5 blend globally."
                    )
                    mix_node.inputs["Fac"].default_value = 0.5
            else:
                # Older games use vertex colors for blending.
                self.link(self.vertex_colors_nodes[0].outputs["Alpha"], mix_node.inputs["Fac"])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        elif material_info.alpha or material_info.edge:
            # Mix single texture Principled BSDF with a Transparent BSDF using vertex alpha.
            # TODO: Assumes single BSDF; will not render second texture slot at all. Confirm 'M' shaders never use Alp.
            #  If they do, need to figure out what defines transparency rather than blending. (Pretty sure this does
            #  happen in later games like ER.)
            transparent_node = self.new("ShaderNodeBsdfTransparent", location=(self.BSDF_X, self.bsdf_y))
            mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.MIX_Y))
            self.link(transparent_node.outputs["BSDF"], mix_node.inputs[1])
            self.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[2])  # more vertex alpha -> more opacity
            self.link(self.vertex_colors_nodes[0].outputs["Alpha"], mix_node.inputs["Fac"])
            self.link_to_output_surface(mix_node.outputs["Shader"])
        else:
            self.link_to_output_surface(bsdf_nodes[0].outputs["BSDF"])

        if "LIGHTMAP" in self.tex_image_nodes:
            # Use an overlay node to mix each non-normal input texture with lightmap.
            lightmap_node = self.tex_image_nodes["LIGHTMAP"]
        else:
            lightmap_node = None

        for common_type, sampler_name in material_info.SAMPLER_NAMES._asdict().items():
            if common_type not in self.tex_image_nodes:
                continue
            bsdf_node = bsdf_nodes[1] if common_type.endswith("_1") else bsdf_nodes[0]
            if bsdf_node is None:
                raise MaterialCreationError(f"Bad state: no BSDF node found for sampler '{common_type}'.")
            tex_image_node = self.tex_image_nodes[common_type]
            if lightmap_node:
                overlay_node_y = tex_image_node.location[1]
                overlay_node = self.new(
                    "ShaderNodeMixRGB", location=(self.POST_TEX_X, overlay_node_y), blend_type="OVERLAY"
                )
                self.link(tex_image_node.outputs["Color"], overlay_node.inputs["Color1"])
                self.link(lightmap_node.outputs["Color"], overlay_node.inputs["Color2"])  # order is important!
                color_output = overlay_node.outputs["Color"]
            else:
                color_output = tex_image_node.outputs["Color"]

            if material_info.alpha or material_info.edge and common_type.startswith("ALBEDO"):
                # We only use the alpha channel of the albedo texture for transparency if the shader supports it. We do
                # NOT want to use alpha otherwise, as some textures lazily use transparent texture regions as black.
                alpha_output = tex_image_node.outputs["Alpha"]
            else:
                alpha_output = None
            self.color_to_bsdf_node(
                y=tex_image_node.location[1],
                common_type=common_type,
                sampler_name=sampler_name,
                color_output=color_output,
                bsdf_node=bsdf_node,
                alpha_output=alpha_output,
            )

        if "DISPLACEMENT" in self.tex_image_nodes:
            # Texture is an actual height map (not just normals).
            disp_node = self.tex_image_nodes["DISPLACEMENT"]
            # TODO: In my observation so far, this always uses UVTexture0 (i.e. never the second texture).
            self.link(self.uv_nodes["UVTexture0"].outputs["Vector"], disp_node.inputs["Vector"])
            self.link_to_output_displacement(disp_node.outputs["Color"])

        for common_type, bsdf_node in zip(("NORMAL_0", "NORMAL_1"), bsdf_nodes):
            sampler_name = material_info.SAMPLER_NAMES.get(common_type)
            if (
                not sampler_name
                or common_type not in self.tex_image_nodes
                or sampler_name not in material_info.sampler_names
            ):
                # No normal map for this texture slot.
                continue
            if bsdf_node is None:
                raise MaterialCreationError(f"Bad state: no BSDF node found for sampler '{common_type}'.")

            # Create normal map node.
            normal_tex_node = self.tex_image_nodes[common_type]
            try:
                uv_layer_name = material_info.sampler_name_uv_layers[sampler_name].name
            except KeyError:
                self.operator.warning(
                    f"Normal texture type '{sampler_name}' is missing a UV index in the material shader info. "
                    f"Cannot create normal map node to connect to BDSF.",
                )
                continue
            normal_map_node = self.add_normal_map_node(uv_layer_name, normal_tex_node.location[1])
            self.link(normal_tex_node.outputs["Color"], normal_map_node.inputs["Color"])
            self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    def color_to_bsdf_node(
        self,
        y: int,
        common_type: str,
        sampler_name: str,
        color_output: bpy.types.NodeSocketColor,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
        alpha_output: bpy.types.NodeSocketFloat = None,
    ):
        if common_type.startswith("SPECULAR"):
            # Split specular texture into specular/roughness channels.
            self.specular_to_principled(
                y,
                color_output,
                bsdf_node,
                is_metallic="Metallic" in sampler_name,
            )
        elif common_type.startswith("ALBEDO"):
            self.link(color_output, bsdf_node.inputs["Base Color"])
            if alpha_output:
                # Plug diffuse alpha into BSDF alpha (no lightmap overlay).
                self.link(alpha_output, bsdf_node.inputs["Alpha"])
        elif common_type.startswith("SHEEN"):
            self.link(color_output, bsdf_node.inputs[PRINCIPLED_SHEEN_INPUT])

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
            self.operator.warning("Cannot yet set up Blender shader for more than three texture groups.")

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

        for tex_image_node in self.tex_image_nodes.values():
            # TODO: Elden Ring sampler names contain key phrases like 'AlbedoMap' but also a ton of other information.
            #  Currently not dealing with it and using the node labels.
            if tex_image_node.image is None:
                tex_image_node.hide = True
                continue  # no shader setup
            sampler_name = tex_image_node.label
            group_index = material_info.sampler_uv_groups[sampler_name]
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

            if "AlbedoMap" in sampler_name:
                self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            if "MetallicMap" in sampler_name:
                self.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Metallic"])
            if "NormalMap" in sampler_name:
                try:
                    uv_layer_name = material_info.sampler_name_uv_layers[sampler_name].name
                except KeyError:
                    self.operator.warning(
                        f"Normal sampler '{sampler_name}' is missing a UV index in the material shader info. "
                        f"Cannot create normal map node to connect to BDSF.",
                    )
                    continue
                normal_map_node = self.add_normal_map_node(uv_layer_name, tex_image_node.location[1])
                self.link(tex_image_node.outputs["Color"], normal_map_node.inputs["Color"])
                self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    # region Texture Input Methods

    def specular_to_principled(
        self,
        y: int,
        color_output: bpy.types.NodeSocketColor,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
        is_metallic=False,
    ):
        """Split color channels of a specular texture into Principled BSDF inputs."""

        separate_color_node = self.new("ShaderNodeSeparateColor", location=(self.POST_TEX_X, y))
        red_math_node = self.new(
            "ShaderNodeMath",
            location=(self.POST_TEX_X, y - 150),
            name="Inverted Red",
            operation="SUBTRACT",
            input_defaults={0: 1.0},
        )
        green_math_node = self.new(
            "ShaderNodeMath",
            location=(self.POST_TEX_X, y - 200),
            name="Inverted Green",
            operation="SUBTRACT",
            input_defaults={0: 1.0},
        )

        self.link(color_output, separate_color_node.inputs["Color"])
        self.link(separate_color_node.outputs["Red"], red_math_node.inputs[1])
        self.link(separate_color_node.outputs["Green"], green_math_node.inputs[1])
        red_input = "Metallic" if is_metallic else PRINCIPLED_SPECULAR_INPUT
        self.link(red_math_node.outputs["Value"], bsdf_node.inputs[red_input])
        self.link(green_math_node.outputs["Value"], bsdf_node.inputs["Roughness"])
        self.link(separate_color_node.outputs["Blue"], bsdf_node.inputs[PRINCIPLED_TRANSMISSION_INPUT])  # not inverted

        red_math_node.hide = True
        green_math_node.hide = True

    # endregion

    # region Builder Methods

    def new(
        self,
        node_type: str,
        location: tuple[int, int] = None,
        /,
        input_defaults: dict[str | int, tp.Any] = None,
        **kwargs,
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

    def link(self, node_output: bpy.types.NodeSocket, node_input: bpy.types.NodeSocket) -> bpy.types.NodeLink:
        return self.tree.links.new(node_output, node_input)

    def link_to_output_surface(self, node_output: bpy.types.NodeSocket) -> bpy.types.NodeLink:
        return self.link(node_output, self.output.inputs["Surface"])

    def link_to_output_volume(self, node_output: bpy.types.NodeSocket) -> bpy.types.NodeLink:
        return self.link(node_output, self.output.inputs["Volume"])

    def link_to_output_displacement(self, node_output: bpy.types.NodeSocket) -> bpy.types.NodeLink:
        return self.link(node_output, self.output.inputs["Displacement"])

    def add_vertex_colors_node(self, index: int) -> bpy.types.Node:
        return self.new(
            "ShaderNodeAttribute",
            location=(self.POST_TEX_X, 1200 + index * 200),
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

    def add_tex_image_node(self, name: str, image: bpy.types.Image | None, label: str = None):
        node = self.new(
            "ShaderNodeTexImage",
            location=(self.TEX_X, self.tex_y),
            image=image,
            name=name,
            label=label or name,
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
            location=(self.POST_TEX_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": 0.4},
        )

    # endregion
