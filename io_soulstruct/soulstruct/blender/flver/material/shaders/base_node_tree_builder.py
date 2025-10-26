from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

import re
import typing as tp
from dataclasses import dataclass, field

import bpy
from bpy.types import NodeSocket

from soulstruct.base.models.shaders import MatDef, MatDefSampler
from soulstruct.games import *
from soulstruct.utilities.maths import Vector2

from soulstruct.blender.exceptions import MaterialImportError
from soulstruct.blender.flver.image.utilities import find_or_create_image
from soulstruct.blender.utilities.files import ADDON_PACKAGE_PATH
from soulstruct.blender.utilities.operators import LoggingOperator

from .enums import *
from .node_groups import create_node_groups, try_add_node_group
from .node_tree import new_shader_node


@dataclass(slots=True)
class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials.

    Manages state intended for one single `context` and one `build()` call.
    """

    operator: LoggingOperator
    context: bpy.types.Context
    material: bpy.types.Material
    matdef: MatDef
    sampler_texture_stems: dict[str, str]  # already combined from MATBIN (if present) and FLVER
    vertex_color_count: int

    # Updated as nodes are added.
    uv_y: int = 1000
    tex_y: int = 1000
    bsdf_y: int = 1000
    mix_y: int = 300  # lower down

    # Maps vertex color layer names (e.g. 'VertexColor0') to Nodes. (Remember that these are actually LOOP colors.)
    vertex_colors_nodes: list[bpy.types.Node] = field(default_factory=list)
    # Maps UV global layer names (e.g. 'UVTexture0') to Nodes.
    uv_nodes: dict[str, bpy.types.Node] = field(default_factory=dict)
    # Maps common, non-game-specific sampler type (e.g. 'Main 0 Albedo') to Nodes.
    tex_image_nodes: dict[str, bpy.types.Node] = field(default_factory=dict)

    tree: bpy.types.NodeTree = field(init=False)
    output: bpy.types.Node = field(init=False)

    # X coordinates of node type columns.
    VERTEX_COLORS_X: tp.ClassVar[int] = -950
    UV_X: tp.ClassVar[int] = -950
    SCALE_X: tp.ClassVar[int] = -750
    TEX_X: tp.ClassVar[int] = -550
    POST_TEX_X: tp.ClassVar[int] = -250  # overlay, split, math, normal map, etc.
    BSDF_X: tp.ClassVar[int] = -50
    MIX_X: tp.ClassVar[int] = 100

    def __post_init__(self):
        self.tree = self.material.node_tree
        self.output = self.tree.nodes["Material Output"]

        # This will create node groups in Blender data (`bpy.data.node_groups`) if not already present.
        create_node_groups()

    def build(self):
        """Build a shader node tree using shader/sampler information from given `MatDef`."""

        self._initialize_node_tree()

        try:
            if self.matdef.shader_category == "Water":
                self._build_water_shader()
                return
            elif self.matdef.shader_category == "Snow":
                self._build_snow_shader()
                return
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building special shader for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )
            return

        try:
            # Generic builder for all other unhandled material categories.
            self._build_shader()
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building shader for material '{self.matdef.name}' with shader '{self.matdef.shader_stem}'. "
                f"Error:\n    {ex}"
            )


    # pow(2.0 / (max(fSpecPower * 4.0, 1.0) + 2.0), 0.25) for converting spec power to roughness from StaydMcMuffin

    def build_shader_uv_texture_nodes(self):
        """Build UV and texture nodes. Used by all games."""

        self.uv_nodes = {}
        self.tex_image_nodes = {}  # type: dict[str, bpy.types.ShaderNodeTexImage]
        uv_scale_nodes = {}

        # We add Image Texture nodes in `MatDef` order, not FLVER order.
        # This is because in later games, MatDef samplers are already nicely grouped together from metaparam.

        current_sampler_group = self.matdef.samplers[0].sampler_group
        for sampler in self.matdef.samplers:

            # NOTE: We create UV texture nodes even for samplers with `is_uv_unused = True`, just so the material is
            # properly represented as it exists in the MTD/MATBIN. The FLVER exporter checks the MTD/MATBIN again and
            # does not care if these nodes are present.

            uv_layer_name = sampler.uv_layer_name
            # We assign the sampler alias to the node label, but preserve the game-specific sampler name in the node
            # name for inspection. The alias label is useful for porting this FLVER with its material to other games.
            node_name = sampler.name
            node_label = sampler.alias  # will be the same as `name` if alias could not be determined by `MatDef`

            if sampler.sampler_group != current_sampler_group:
                # Add extra Y offset to visually separate new group.
                self.tex_y -= 100
                current_sampler_group = sampler.sampler_group

            bl_image = self.get_sampler_bl_image(sampler.name)
            tex_image_node = self._new_tex_image_node(
                name=node_name, image=bl_image, label=node_label, hide=bl_image is None
            )

            # Dictionary keys are sampler aliases, not game-specific sampler names (though alias may fall back to that).
            self.tex_image_nodes[node_label] = tex_image_node

            # We take this opportunity to change the Color Space of non-Albedo textures to 'Non-Color'.
            # NOTE: If the texture is used inconsistently across materials, this could change repeatedly.
            if bl_image and "Albedo" not in node_label and "Lightmap" not in node_label:
                bl_image.colorspace_settings.name = "Non-Color"
            if uv_layer_name:
                # Connect to appropriate UV node, creating it if necessary.
                if uv_layer_name in self.uv_nodes:
                    uv_node = self.uv_nodes[uv_layer_name]
                else:
                    uv_node = self.uv_nodes[uv_layer_name] = self._new_uv_node(uv_layer_name)
                if sampler.uv_scale is not None:
                    # Elden Ring materials define extra scaling for certain sampler groups. We replicate it to produce
                    # a more faithful shader in Blender. None of this is exported to FLVER.
                    if sampler.sampler_group >= 1:
                        # Non-zero groups share UV scale, and so they share one node here.
                        if sampler.sampler_group in uv_scale_nodes:
                            uv_scale_node = uv_scale_nodes[sampler.sampler_group]
                        else:
                            # First occurrence of group. Create UV scale node.
                            uv_scale_node = self._new_tex_scale_node(sampler.uv_scale, tex_image_node.location.y)
                            uv_scale_nodes[sampler.sampler_group] = uv_scale_node
                    else:
                        # Group 0 should never have UV scale defined in MATBIN params, but just in case...
                        uv_scale_node = self._new_tex_scale_node(sampler.uv_scale, tex_image_node.location.y)
                    self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
                    self.link(uv_scale_node.outputs["Vector"], tex_image_node.inputs["Vector"])
                else:
                    self.link(uv_node.outputs["Vector"], tex_image_node.inputs["Vector"])

        # Finally, add unrecognized samplers.
        matdef_sampler_names = {sampler.name for sampler in self.matdef.samplers}
        for sampler_name, texture_stem in self.sampler_texture_stems.items():
            if sampler_name in matdef_sampler_names:
                continue
            self.tex_y -= 100  # space these out a bit more
            bl_image = self.get_sampler_bl_image(sampler_name)
            tex_image_node = self._new_tex_image_node(
                name=sampler_name, image=bl_image, label=sampler_name, hide=bl_image is None
            )
            self.tex_image_nodes[sampler_name] = tex_image_node

    def _build_water_shader(self):
        """Check for common special shader types, like water, that are present across games.

        Returns `True` if a special shader was found and handled.
        """
        # Special simplified shader. Uses 'g_Bumpmap' only.
        transparent = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeBsdfTransparent,
            (self.BSDF_X, self.mix_y),
        )
        glass = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeBsdfGlass,
            (self.BSDF_X, 1000),
            inputs={"IOR": 1.333},
        )

        normal_node = self.tex_image_nodes["Main 0 Normal"]
        try:
            uv_texture_0 = self.matdef.UVLayer["UVTexture0"].name
        except KeyError:
            raise MaterialImportError(
                "This `MatDef` game subclass does not define 'UVTexture0' layer, which is required for water shader."
            )

        self._new_normal_map_node(
            uv_texture_0,
            normal_node.location[1],
            inputs={"Color": normal_node.outputs["Color"]},
            outputs={"Normal": glass.inputs["Normal"]},
        )

        new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMixShader,
            (self.MIX_X, self.mix_y),
            inputs={
                "Fac": self.vertex_colors_nodes[0].outputs["Alpha"],
                1: transparent.outputs[0],
                2: glass.outputs[0],
            },
            outputs={0: self.output_surface},
        )

    def _build_snow_shader(self):
        """
        Sketch for DS1R snow shader:
         - Mix a standard Principled BSDF (main texture, e.g. ground) and a Diffuse BSDF shader for snow.
         - Use 'Main 0 Albedo' and 'Main 0 Specular' as usual for Principled.
             - Mix 'Lightmap' as overlay if present.
         - Snow diffuse uses both 'Main 0 Normal' (which is sometimes a diffuse snow texture!) and 'Main 1 Normal' as
           its BSDF normal input (mapped with UVTexture0). We mix these two textures 50/50 if given.
         - 'Main 2 Normal' is actually the normal map for the Principled BSDF, but only appears in DS1R! Not PTDE.
         - Mix shader nodes using vertex color alpha, raised with a Math node to the power of 4.0, which seems to
           capture the snow effect best in my tuning.
         - Create a Mix Shader for the standard textures and new Diffuse snow BSDF. Plug into material output.
        """

        bsdf_node = self._new_principled_bsdf_node("Main 0 BSDF")
        # noinspection PyTypeChecker
        diffuse_bsdf_node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeBsdfDiffuse, location=(self.BSDF_X, self.bsdf_y)
        )  # type: bpy.types.ShaderNodeBsdfDiffuse
        self.bsdf_y -= 1000

        # Raise vertex alpha to the power of 2.0 and use as mix Fac.
        vertex_alpha_power = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMath,
            location=(self.BSDF_X, self.mix_y),
            inputs={
                0: self.vertex_colors_nodes[0].outputs["Alpha"],
                1: 2.0,
            },
            operation=MathOperation.POWER,
        )

        # Mix Principled BSDF 0 with snow diffuse.
        new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMixShader,
            (self.MIX_X, self.mix_y),
            inputs={
                "Fac": vertex_alpha_power.outputs["Alpha"],
                1: bsdf_node.outputs["BSDF"],
                2: diffuse_bsdf_node.outputs["BSDF"],
            },
            outputs={0: self.output_surface},
        )

        # Create lightmap if present.
        lightmap_node = self.tex_image_nodes.get("Lightmap", None)

        # Connect standard textures to Principled BSDF.
        main_sampler_re = re.compile(r".* (Albedo|Specular|Shininess|Normal)")
        for _, sampler in self.matdef.get_matching_samplers(main_sampler_re, match_alias=True):
            if sampler.alias not in self.tex_image_nodes:
                continue
            self._color_tex_to_bsdf_node(
                sampler=sampler,
                tex_image_node=self.tex_image_nodes[sampler.alias],
                bsdf_node=bsdf_node,
                lightmap_node=lightmap_node,
            )

        # NOTE: I don't think snow shaders EVER use displacement, but may as well check and handle it.
        if "Displacement" in self.tex_image_nodes:
            disp_node = self.tex_image_nodes["Displacement"]
            self.link(self.uv_nodes["UVTexture0"].outputs["Vector"], disp_node.inputs["Vector"])
            self.link(disp_node.outputs["Color"], self.output_displacement)

        # Connect 'Main 0 Normal' (snow diffuse color) and 'Main 1 Normal' (snow diffuse normal) to diffuse node.
        # TODO: Snow albedo texture is used with 'g_Bumpmap' for this shader! We just use it as albedo here.
        snow_albedo_node = self.tex_image_nodes["Main 0 Normal"]
        self.link(snow_albedo_node.outputs["Color"], diffuse_bsdf_node.inputs["Color"])
        # TODO: Snow MTD (in DS1R at least) incorrectly says to use UV index 1 for snow normal map, but that UV
        #  layer doesn't even exist on the meshes that use it. MTD for DS1R should already fix that, but we force
        #  'UVTexture0' here anyway to be safe, given the specificity of this code.
        tex_image_node = self.tex_image_nodes["Main 1 Normal"]
        self._normal_tex_to_normal_input(
            y=tex_image_node.location[1],
            color_input_from=tex_image_node.outputs["Color"],
            normal_output_to=diffuse_bsdf_node.inputs["Normal"],
            uv_layer_name="UVTexture0",
        )

        if "Main 2 Normal" in self.tex_image_nodes:
            # Only known use of 'Main 2 Normal' in DS1R, and it's the normal map of the main texture (e.g. ground).
            normal_tex_node = self.tex_image_nodes["Main 2 Normal"]
            self._normal_tex_to_normal_input(
                normal_tex_node.location[1],
                normal_tex_node.outputs["Color"],
                bsdf_node.inputs["Normal"],
                uv_layer_name="UVTexture0",
            )

    def _build_shader(self):
        """Fallback method for any shader that doesn't have a special case.
        
        Base method here tries to build a cross-game standard using sampler aliases like 'Main 0 Albedo'.

        TODO: Biggest improvements here would be adjusting overall specularity for Wood, Stone, etc.
        """

        # Get special nodes, if they exist.
        blend01_node = self.tex_image_nodes.get("Blend 01", None)
        lightmap_node = self.tex_image_nodes.get("Lightmap", None)

        # We create one BSDF node per 'texture group' (Albedo slot) and mix all groups afterward.
        bsdf_nodes = {}  # type: dict[str, bpy.types.Node]
        tex_sampler_re = re.compile(r"(Main|Detail) (\d+) (Albedo|Specular|Shininess|Normal)")

        # Special case: if an Albedo map using 'UVFur' is found, we pass its alpha to ALL BSDFs.
        # TODO: Pretty sure I may want to do this for 'first group' in Elden Ring in general.
        fur_albedo_alpha = None  # type: NodeSocket | None

        for match, sampler in self.matdef.get_matching_samplers(tex_sampler_re, match_alias=True):
            tex_node = self.tex_image_nodes.get(sampler.alias, None)
            if tex_node and tex_node.image:
                # We only create BSDF nodes for textures that are actually used.
                bsdf_key = f"{match.group(1)} {match.group(2)}"
                map_type = match.group(3)
                try:
                    bsdf_node = bsdf_nodes[bsdf_key]
                except KeyError:
                    bsdf_node = bsdf_nodes[bsdf_key] = self._new_principled_bsdf_node(f"{bsdf_key} BSDF")

                if fur_albedo_alpha is None and sampler.uv_layer_name == "UVFur":
                    # This alpha will be used for all BSDFs.
                    fur_albedo_alpha = tex_node.outputs["Alpha"]

                if map_type == "Normal":
                    # Intervening Normal Map node required with appropriate UV layer.
                    # TODO: Some groups only have normal maps. How do I mix this? White albedo? Or `color` MATBIN param?
                    self._normal_tex_to_normal_input(
                        tex_node.location[1],
                        tex_node.outputs["Color"],
                        bsdf_node.inputs["Normal"],
                        uv_layer_name=sampler.uv_layer_name,
                    )
                else:
                    # Color multiple with lightmap, if present, and channels are split/flipped as appropriate.
                    # TODO: Main texture ALPHA should override any detail BSDF, rather than mixing with it (ER).
                    self._color_tex_to_bsdf_node(
                        sampler=sampler,
                        tex_image_node=self.tex_image_nodes[sampler.alias],
                        bsdf_node=bsdf_node,
                        lightmap_node=lightmap_node,
                        bsdf_alpha_input=fur_albedo_alpha,
                    )

        if not bsdf_nodes:
            self.operator.warning("Could not find any used textures to connect to any BSDF in Blender shader.")
            return

        # Mix all BSDF nodes together. TODO: May be incomplete, and finished manually, while I figure it out.
        nodes_to_mix = list(bsdf_nodes.keys())

        # First, we mix Main 0 and Main 1 (using Blend 01 or vertex alpha).
        if "Main 0" in nodes_to_mix and "Main 1" in nodes_to_mix:
            # Mix first two Main BSDF nodes using Blend01 or vertex color.
            mix_fac_input = 0.5
            if blend01_node:
                mix_fac_input = blend01_node.outputs["Color"]
            elif self.matdef.get_sampler_with_alias("Blend 01"):
                self.operator.warning(
                    "This material defines a 'Blend 01' sampler, but no 'Blend 01' texture node was found. "
                    "Cannot weight textures in shader; using 0.5 blend globally."
                )
            elif self.vertex_colors_nodes:
                # Older games use vertex colors for blending.
                mix_fac_input = self.vertex_colors_nodes[0].outputs["Alpha"]

            current_last_shader = self._mix_shader_nodes(
                bsdf_nodes["Main 0"].outputs[0],
                bsdf_nodes["Main 1"].outputs[0],
                mix_fac_input,
            )
            nodes_to_mix.remove("Main 0")
            nodes_to_mix.remove("Main 1")
            # All other nodes in `nodes_to_mix` will be mixed with this mix shader.
        else:
            # Just mix in BSDF order.
            current_last_shader = bsdf_nodes[nodes_to_mix[0]]

        for i, shader_node_name in enumerate(nodes_to_mix[1:]):
            # If there is only one BSDF (or the Main mix from above), this loop won't run.

            # TODO: Currently just mixing any additional Main textures 0.5 with last mix.
            shader_node = bsdf_nodes[shader_node_name]
            if shader_node_name.startswith("Main "):
                current_last_shader = self._mix_shader_nodes(
                    current_last_shader.outputs[0],
                    shader_node.outputs[0],
                    0.5,
                )
            else:
                # Mix all Detail BSDF nodes together using weight parameters.
                # TODO: Until I figure out the MATBIN weight parameters, just mix them all evenly.
                current_last_shader = self._mix_shader_nodes(
                    current_last_shader.outputs[0],
                    shader_node.outputs[0],
                    0.5,
                )
            current_last_shader.hide = True
            current_last_shader.location.x += i * 40.0

        if len(bsdf_nodes) == 1 and (self.matdef.alpha or self.matdef.edge):
            # Older games: mix current last shader with a Transparent BSDF using vertex alpha.
            # TODO: Does Elden Ring ever do this using an alpha blend mask?
            transparent_node = new_shader_node(
                self.tree, bpy.types.ShaderNodeBsdfTransparent, location=(self.BSDF_X, self.bsdf_y)
            )
            # Note mix order here, so Fac 0 = fully transparent, Fac 1 = fully opaque.
            current_last_shader = self._mix_shader_nodes(
                transparent_node.outputs[0],
                current_last_shader.outputs[0],
                self.vertex_colors_nodes[0].outputs["Alpha"] if self.vertex_colors_nodes else 0.5,
            )

        self.link(current_last_shader.outputs[0], self.output_surface)  # last shader could be a BSDF or Mix Shader

        if "Displacement" in self.tex_image_nodes:
            # Texture is an actual height map (not just normals).
            disp_node = self.tex_image_nodes["Displacement"]
            # TODO: In my observation so far (DS1), this always uses UVTexture0 (i.e. never the second texture).
            self.link(self.uv_nodes["UVTexture0"].outputs["Vector"], disp_node.inputs["Vector"])
            self.link(disp_node.outputs["Color"], self.output_displacement)

        # Any BSDFs with no Albedo input use OPAQUE BLACK, not default WHITE.
        for bsdf_node in bsdf_nodes.values():
            if not bsdf_node.inputs["Base Color"].is_linked:
                bsdf_node.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)

    def _build_primary_shader(self,
                              node_group_name: str,
                              node_inputs: dict,
                              mtd_param_values: dict,
                              ):
        """
        Outline for this:
            Generalize all the logic for connecting values into a node group. Really, all that happens is:
            - image color outputs get connected.
            - normal map gets processed, then connected
            - image alpha outputs get connected
            - vertex color gets linked
            - vertex alpha gets linked
            - mtd params/lightmap influence/other values get filled directly
            To be even more general, it's just node links, and static values to be set.
            This is to prevent duplicating/maintaining duplicate code.
        """

        node_group_inputs = {}
        for key in node_inputs:
            if node_inputs[key] is not None:
                node_group_inputs[key] = node_inputs[key]

        node_group = self._new_bsdf_shader_node_group(node_group_name, inputs=node_group_inputs)
        for key in mtd_param_values:
            node_group.inputs[key].default_value = mtd_param_values[key]

        self.link(node_group.outputs[0], self.output_surface)

    def _initialize_node_tree(self):
        # Remove all node links.
        self.tree.links.clear()
        # Remove all nodes except Material Output.
        for node in tuple(self.tree.nodes):
            if node.name != "Material Output":
                self.tree.nodes.remove(self.tree.nodes["Principled BSDF"])

        # Build vertex color nodes.
        self.vertex_colors_nodes = [
            self._add_vertex_colors_node(i) for i in range(self.vertex_color_count)
        ]

        try:
            self.build_shader_uv_texture_nodes()
        except KeyError as ex:
            raise MaterialImportError(
                f"Could not build UV coordinate nodes for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )

    def _color_tex_to_bsdf_node(
        self,
        sampler: MatDefSampler,
        tex_image_node: bpy.types.ShaderNodeTexImage,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
        lightmap_node: bpy.types.ShaderNodeTexImage | None = None,
        bsdf_alpha_input: NodeSocket | None = None,
    ):
        if lightmap_node:
            overlay_node_y = tex_image_node.location[1]
            overlay_node = new_shader_node(
                self.tree,
                bpy.types.ShaderNodeMixRGB, location=(self.POST_TEX_X, overlay_node_y), blend_type="OVERLAY"
            )
            self.link(tex_image_node.outputs["Color"], overlay_node.inputs["Color1"])
            self.link(lightmap_node.outputs["Color"], overlay_node.inputs["Color2"])  # order is important!
            color_output = overlay_node.outputs["Color"]
        else:
            color_output = tex_image_node.outputs["Color"]

        if sampler.alias.endswith("Specular"):
            # Split specular texture into specular/roughness channels.
            self._specular_tex_to_bsdf_principled_node(
                y=tex_image_node.location[1] - 150,  # leave room for overlay node
                specular_tex_color=color_output,
                bsdf_node=bsdf_node,
                is_metallic="Metallic" in sampler.name,  # different BSDF parameter used in later games
            )
        elif sampler.alias.endswith("Albedo"):
            self.link(color_output, bsdf_node.inputs["Base Color"])

            if bsdf_alpha_input:
                # Manual input for BSDF alpha (e.g. fur albedo).
                self.link(bsdf_alpha_input, bsdf_node.inputs["Alpha"])
            elif "_snp_" in sampler.name or self.matdef.alpha or self.matdef.edge:
                # We only use the alpha channel of the albedo texture for transparency if the shader supports it. We do
                # NOT want to use alpha otherwise, as some textures lazily use transparent texture regions as black.
                # NOTE: Currently assuming that all Elden Ring albedo textures support transparency.
                self.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])

        elif sampler.alias.endswith("Shininess"):
            self.link(color_output, bsdf_node.inputs["Sheen Weight"])

    def _mix_shader_nodes(
        self,
        input_1: NodeSocket,
        input_2: NodeSocket,
        mix_fac_input: NodeSocket | float = 0.5,
    ) -> bpy.types.ShaderNodeMixShader:
        mix_node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMixShader,
            (self.MIX_X, self.mix_y),
            inputs={
                "Fac": mix_fac_input,
                1: input_1,
                2: input_2,
            },
        )
        self.mix_y -= 100
        return mix_node

    def _mix_value_nodes(
        self,
        input_1: NodeSocket,
        input_2: NodeSocket,
        node_y: int,
        mix_fac_input: NodeSocket | float = 0.5,
        mix_data_type: str = "VECTOR"
    ) -> bpy.types.ShaderNodeMix:
        mix_node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMix,
            (self.POST_TEX_X, node_y),
            inputs={
                "Factor": mix_fac_input,
                "A": input_1,
                "B": input_2,
            },
            data_type=mix_data_type
        )

        return mix_node

    def _get_single_or_mixed_samplers(self, pattern: str, mix_fac_input: NodeSocket | float = 0.5, alpha: bool = False, normal: bool = False):
        matches = self.matdef.get_matching_samplers(re.compile(pattern), match_alias=True)
        if len(matches) >= 2:
            tex_node1 = self.tex_image_nodes.get(matches[0][1].alias)
            tex_node2 = self.tex_image_nodes.get(matches[1][1].alias)
            if alpha:
                return self._mix_value_nodes(tex_node1.outputs["Alpha"], tex_node2.outputs["Alpha"],
                                             tex_node1.location[1] - 50,
                                             mix_fac_input, "FLOAT").outputs["Result"]
            elif normal:
                _, normal_map_node1 = self._normal_tex_to_normal_input(
                    y=tex_node1.location[1],
                    color_input_from=tex_node1.outputs["Color"],
                    normal_output_to=None,
                    uv_layer_name=matches[0][1].uv_layer_name
                )
                _, normal_map_node2 = self._normal_tex_to_normal_input(
                    y=tex_node2.location[1],
                    color_input_from=tex_node2.outputs["Color"],
                    normal_output_to=None,
                    uv_layer_name=matches[1][1].uv_layer_name
                )

                return self._mix_value_nodes(normal_map_node1.outputs["Normal"], normal_map_node2.outputs["Normal"],
                                             tex_node1.location[1],
                                             mix_fac_input, "VECTOR").outputs["Result"]
            else:
                return self._mix_value_nodes(tex_node1.outputs["Color"], tex_node2.outputs["Color"],
                                             tex_node1.location[1],
                                             mix_fac_input, "RGBA").outputs["Result"]
        elif len(matches) == 1:
            match = self.tex_image_nodes.get(matches[0][1].alias)
            if alpha:
                return self.tex_image_nodes.get(matches[0][1].alias).outputs["Alpha"]
            elif normal:
                _, normal_map_node = self._normal_tex_to_normal_input(
                    y=match.location[1],
                    color_input_from=match.outputs["Color"],
                    normal_output_to=None,
                    uv_layer_name=matches[0][1].uv_layer_name
                )
                return normal_map_node.outputs["Normal"]
            else:
                return match.outputs["Color"]
        else:
            return None




    def get_sampler_bl_image(self, sampler_name: str) -> bpy.types.Image | None:
        """All Blender Images from textures (cached or DDS) are lower-case names. FLVER paths are not case-sensitive."""
        texture_stem = self.sampler_texture_stems[sampler_name].lower()
        if not texture_stem:
            # No texture given in MATBIN or FLVER.
            return None
        # Search for Blender image with no extension, TGA, PNG, or DDS, in that order of preference.
        return find_or_create_image(self.operator, self.context, texture_stem)

    # region Texture Input Methods

    def _specular_tex_to_bsdf_principled_node(
        self,
        y: float,
        specular_tex_color: NodeSocket,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
        is_metallic=False,
    ):
        """Processes specular map and plugs it into appropriate inputs of Principled BSDF shader node."""

        group_key = "Process Specular"
        if is_metallic:
            group_key += " (Metallic)"

        specular_outputs = {
            "Roughness": bsdf_node.inputs["Roughness"],
            "Transmission Weight": bsdf_node.inputs["Transmission Weight"],
        }
        if is_metallic:
            specular_outputs["Metallic"] = bsdf_node.inputs["Metallic"]
        else:
            specular_outputs["Specular IOR Level"] = bsdf_node.inputs["Specular IOR Level"]

        new_shader_node(
            self.tree,
            bpy.types.ShaderNodeGroup,
            location=(self.POST_TEX_X, y),
            node_tree=bpy.data.node_groups[group_key],
            name=group_key,
            label="Process Specular",
            inputs={"Color": specular_tex_color},
            outputs=specular_outputs,
        )

    def _normal_tex_to_normal_input(
        self,
        y: float,
        color_input_from: NodeSocket | None,
        normal_output_to: NodeSocket | None,
        uv_layer_name: str,
    ) -> tuple[bpy.types.ShaderNodeGroup, bpy.types.ShaderNodeNormalMap]:
        """Create a node group that processes input normal map colors (for given game) to Blender normal colors.

        Blender expects red to be the X component (right positive), green to be the Y component (up positive), and blue
        to be the Z component. It also expects the color range [0, 1] to actually represent the normal range [-1, 1],
        i.e. uses a full spherical mapping.

        Most FromSoft games use standard DX format RGB normal maps. We only need to flip the G channel to convert to
        Blender's expected OpenGL format. DSR uses a hemispherical RG normal map with B implicit from normalization
        (given convexity). We need to invert the G channel and compute the B channel to convert to the OpenGL format.

        TODO: From memory, Elden Ring normal map B channel is actually Shininess?
        """
        settings = self.context.scene.soulstruct_settings

        group_key = "Flip Green, Compute Blue" if settings.is_game(DARK_SOULS_DSR) else "Flip Green"
        group_node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeGroup,
            location=(self.POST_TEX_X, y),
            inputs={"Color": color_input_from},
            node_tree=bpy.data.node_groups[group_key],
            name=group_key,
            label="Process Normals",
        )

        # Create normal map node and link processing group output to it, and output normal map node to BSDF.
        normal_map_node = self._new_normal_map_node(
            uv_layer_name,
            y - 120,
            strength=1.0,
            inputs={"Color": group_node.outputs["Normal"]},
            outputs={"Normal": normal_output_to},
        )
        normal_map_node.hide = True

        return group_node, normal_map_node

    # endregion

    # region Builder Methods

    def get_mtd_param(self, mtd_param_name: str, default=None) -> bool | int | list[int] | float | list[float]:
        return self.matdef.mtd.get_param(mtd_param_name, default)

    def link(self, node_output: NodeSocket, node_input: NodeSocket) -> bpy.types.NodeLink:
        return self.tree.links.new(node_output, node_input)

    @property
    def output_surface(self) -> NodeSocket:
        return self.output.inputs["Surface"]
    
    @property
    def output_volume(self) -> NodeSocket:
        return self.output.inputs["Volume"]

    @property
    def output_displacement(self) -> NodeSocket:
        return self.output.inputs["Displacement"]

    def _add_vertex_colors_node(self, index: int) -> bpy.types.Node:
        return new_shader_node(
            self.tree,
            bpy.types.ShaderNodeAttribute,
            location=(self.POST_TEX_X, 1200 + index * 200),
            name=f"VertexColors{index}",
            attribute_name=f"VertexColors{index}",
        )

    def _new_uv_node(self, uv_map_name: str):
        """Create an attribute node for the given UV layer name."""
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeAttribute,
            location=(self.UV_X, self.uv_y),
            name=uv_map_name,
            attribute_name=uv_map_name,
            label=uv_map_name,
        )
        self.uv_y -= 1000
        return node

    def _new_tex_scale_node(self, scale: Vector2, node_y: float):
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeVectorMath,
            location=(self.SCALE_X, node_y),
            operation="MULTIPLY",
            label="UV Scale",
        )
        node.inputs[1].default_value = [scale.x, scale.y, 1.0]
        return node

    def _new_normal_combine_node(
        self,
        node_y: float,
        inputs: dict[str | int, tp.Any] = None,
        outputs: dict[str | int, tp.Any] = None,
    ):
        try_add_node_group("Combine Detail")
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeGroup,
            location=(self.POST_TEX_X, node_y),
            inputs=inputs,
            outputs=outputs,
            node_tree=bpy.data.node_groups["Combine Detail"],
        )
        node: bpy.types.ShaderNodeGroup
        return node

    def _new_tex_image_node(
        self, name: str, image: bpy.types.Image | None, label: str = None, hide=False
    ) -> bpy.types.ShaderNodeTexImage:
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeTexImage,
            location=(self.TEX_X, self.tex_y),
            image=image,
            name=name,
            label=label or name,
        )
        if hide:
            node.hide = True
            self.tex_y -= 50  # packed closer together
        else:
            self.tex_y -= 300
        # noinspection PyTypeChecker
        return node

    def _new_principled_bsdf_node(self, bsdf_name: str, label: str = "") -> bpy.types.ShaderNodeBsdfPrincipled:
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeBsdfPrincipled,
            location=(self.BSDF_X, self.bsdf_y),
            name=bsdf_name,
            inputs={"Roughness": 0.75},
            label=label or bsdf_name,
        )
        self.bsdf_y -= 1000
        return node

    def _new_normal_map_node(
        self,
        uv_map_name: str,
        location_y: float,
        strength=1.0,
        inputs: dict[str | int, tp.Any] = None,
        outputs: dict[str | int, tp.Any] = None,
    ) -> bpy.types.ShaderNodeNormalMap:
        return new_shader_node(
            self.tree,
            bpy.types.ShaderNodeNormalMap,
            location=(self.POST_TEX_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            inputs=(inputs or {}) | {"Strength": strength},
            outputs=outputs,
        )

    def _new_bsdf_shader_node_group(
        self,
        node_group_name: str,
        inputs: dict[str | int, tp.Any] = None,
        outputs: dict[str | int, tp.Any] = None,
    ) -> bpy.types.ShaderNodeGroup:
        """Create a new `ShaderNodeGroup` of the given name type, or import it from the packaged blend file.

        Positions group node at the current BSDF_X and bsdf_y, and decrements bsdf_y by 1000.
        """
        try_add_node_group(node_group_name)
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeGroup,
            location=(self.BSDF_X, self.bsdf_y),
            inputs=inputs,
            outputs=outputs,
            node_tree=bpy.data.node_groups[node_group_name],
        )
        node: bpy.types.ShaderNodeGroup
        self.bsdf_y -= 1000
        return node





    # endregion
