from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

import re
import typing as tp
from dataclasses import dataclass, field

import bpy

from soulstruct.base.models.shaders import MatDef, MatDefSampler
from soulstruct.games import *
from soulstruct.utilities.maths import Vector2

from io_soulstruct.exceptions import MaterialImportError
from io_soulstruct.utilities.operators import LoggingOperator


@dataclass(slots=True)
class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials."""

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

        # Remove all node links.
        self.tree.links.clear()
        # Remove all nodes except Material Output.
        for node in tuple(self.tree.nodes):
            if node.name != "Material Output":
                self.tree.nodes.remove(self.tree.nodes["Principled BSDF"])

        # Build vertex color nodes.
        self.vertex_colors_nodes = [
            self.add_vertex_colors_node(i) for i in range(self.vertex_color_count)
        ]

        try:
            self.build_shader_uv_texture_nodes()
        except KeyError as ex:
            raise MaterialImportError(
                f"Could not build UV coordinate nodes for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )

        try:
            if self.matdef.shader_category == "Water":
                self.build_water_shader()
                return
            elif self.matdef.shader_category == "Snow":
                self.build_snow_shader()
                return
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building special shader for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )
            return

        # Build game-dependent or generic shader.
        try:
            self.build_standard_shader(self.matdef)
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building shader for material '{self.matdef.name}' with shader '{self.matdef.shader_stem}'. "
                f"Error:\n    {ex}"
            )

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

            bl_image = self.get_bl_image(sampler.name)
            tex_image_node = self.add_tex_image_node(
                name=node_name, image=bl_image, label=node_label, hide=bl_image is None
            )

            # Dictionary keys are sampler aliases, not game-specific sampler names (though alias may fall back to that).
            self.tex_image_nodes[node_label] = tex_image_node

            # We take this opportunity to change the Color Space of non-Albedo textures to 'Non-Color'.
            # NOTE: If the texture is used inconsistently across materials, this could change repeatedly.
            if bl_image and "Albedo" not in node_label:
                bl_image.colorspace_settings.name = "Non-Color"

            if uv_layer_name:
                # Connect to appropriate UV node, creating it if necessary.
                if uv_layer_name in self.uv_nodes:
                    uv_node = self.uv_nodes[uv_layer_name]
                else:
                    uv_node = self.uv_nodes[uv_layer_name] = self.add_uv_node(uv_layer_name)
                if sampler.uv_scale is not None:
                    # Elden Ring materials define extra scaling for certain sampler groups. We replicate it to produce
                    # a more faithful shader in Blender. None of this is exported to FLVER.
                    if sampler.sampler_group >= 1:
                        # Non-zero groups share UV scale, and so they share one node here.
                        if sampler.sampler_group in uv_scale_nodes:
                            uv_scale_node = uv_scale_nodes[sampler.sampler_group]
                        else:
                            # First occurrence of group. Create UV scale node.
                            uv_scale_node = self.add_tex_scale_node(sampler.uv_scale, tex_image_node.location.y)
                            uv_scale_nodes[sampler.sampler_group] = uv_scale_node
                    else:
                        # Group 0 should never have UV scale defined in MATBIN params, but just in case...
                        uv_scale_node = self.add_tex_scale_node(sampler.uv_scale, tex_image_node.location.y)
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
            bl_image = self.get_bl_image(sampler_name)
            tex_image_node = self.add_tex_image_node(
                name=sampler_name, image=bl_image, label=sampler_name, hide=bl_image is None
            )
            self.tex_image_nodes[sampler_name] = tex_image_node

    def build_water_shader(self) -> bool:
        """Check for common special shader types, like water, that are present across games.

        Returns `True` if a special shader was found and handled.
        """
        # Special simplified shader. Uses 'g_Bumpmap' only.
        water_mix = self.new("ShaderNodeMixShader", (self.MIX_X, self.mix_y))
        transparent = self.new("ShaderNodeBsdfTransparent", (self.BSDF_X, self.mix_y))
        glass = self.new("ShaderNodeBsdfGlass", (self.BSDF_X, 1000), input_defaults={"IOR": 1.333})
        self.link(transparent.outputs[0], water_mix.inputs[1])
        self.link(glass.outputs[0], water_mix.inputs[2])

        normal_node = self.tex_image_nodes["Main 0 Normal"]
        try:
            uv_texture_0 = self.matdef.UVLayer["UVTexture0"].name
        except KeyError:
            raise MaterialImportError(
                "This `MatDef` game subclass does not define 'UVTexture0' layer, which is required for water shader."
            )

        normal_map_node = self.add_normal_map_node(uv_texture_0, normal_node.location[1])
        self.link(normal_node.outputs["Color"], normal_map_node.inputs["Color"])
        self.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
        self.link(self.vertex_colors_nodes[0].outputs["Alpha"], water_mix.inputs["Fac"])
        self.link_to_output_surface(water_mix.outputs[0])
        return True

    def build_snow_shader(self):
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

        bsdf_node = self.add_principled_bsdf_node("Main 0 BSDF")
        # noinspection PyTypeChecker
        diffuse_bsdf_node = self.new(
            "ShaderNodeBsdfDiffuse", location=(self.BSDF_X, self.bsdf_y)
        )  # type: bpy.types.ShaderNodeBsdfDiffuse
        self.bsdf_y -= 1000

        # Mix Principled BSDF 0 with snow diffuse.
        mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.mix_y))
        self.link(bsdf_node.outputs["BSDF"], mix_node.inputs[1])
        self.link(diffuse_bsdf_node.outputs["BSDF"], mix_node.inputs[2])

        # Raise vertex alpha to the power of 2.0 and use as mix Fac.
        vertex_alpha_power = self.new(
            "ShaderNodeMath", location=(self.BSDF_X, self.mix_y), operation="POWER", input_defaults={1: 2.0}
        )
        self.link(self.vertex_colors_nodes[0].outputs["Alpha"], vertex_alpha_power.inputs[0])
        self.link(vertex_alpha_power.outputs[0], mix_node.inputs["Fac"])
        self.link_to_output_surface(mix_node.outputs[0])

        # Create lightmap if present.
        lightmap_node = self.tex_image_nodes.get("Lightmap", None)

        # Connect standard textures to Principled BSDF.
        main_sampler_re = re.compile(r".* (Albedo|Specular|Shininess|Normal)")
        for _, sampler in self.matdef.get_matching_samplers(main_sampler_re, match_alias=True):
            if sampler.alias not in self.tex_image_nodes:
                continue
            self.color_to_bsdf_node(
                sampler=sampler,
                tex_image_node=self.tex_image_nodes[sampler.alias],
                bsdf_node=bsdf_node,
                lightmap_node=lightmap_node,
            )

        # NOTE: I don't think snow shaders EVER use displacement, but may as well check and handle it.
        if "Displacement" in self.tex_image_nodes:
            disp_node = self.tex_image_nodes["Displacement"]
            self.link(self.uv_nodes["UVTexture0"].outputs["Vector"], disp_node.inputs["Vector"])
            self.link_to_output_displacement(disp_node.outputs["Color"])

        # Connect 'Main 0 Normal' (snow diffuse color) and 'Main 1 Normal' (snow diffuse normal) to diffuse node.
        # TODO: Snow albedo texture is used with 'g_Bumpmap' for this shader! We just use it as albedo here.
        snow_albedo_node = self.tex_image_nodes["Main 0 Normal"]
        self.link(snow_albedo_node.outputs["Color"], diffuse_bsdf_node.inputs["Color"])
        # TODO: Snow MTD (in DS1R at least) incorrectly says to use UV index 1 for snow normal map, but that UV
        #  layer doesn't even exist on the meshes that use it. MTD for DS1R should already fix that, but we force
        #  'UVTexture0' here anyway to be safe, given the specificity of this code.
        self.normal_tex_to_bsdf_node(self.tex_image_nodes["Main 1 Normal"], "UVTexture0", diffuse_bsdf_node)

        if "Main 2 Normal" in self.tex_image_nodes:
            # Only known use of 'Main 2 Normal' in DS1R, and it's the normal map of the main texture (e.g. ground).
            self.normal_tex_to_bsdf_node(self.tex_image_nodes["Main 2 Normal"], "UVTexture0", bsdf_node)

    def build_standard_shader(self, matdef: MatDef):
        """Build cross-game, standard types of shaders using sampler aliases like 'Main 0 Albedo'.

        Returns `True` if a generic shader was found and handled.

        TODO: Biggest improvements here would be adjusting overall specularity for Wood, Stone, etc.

        TODO: Use node groups for each BSDF and its sampler inputs.
        """

        # Get special nodes, if they exist.
        blend01_node = self.tex_image_nodes.get("Blend 01", None)
        lightmap_node = self.tex_image_nodes.get("Lightmap", None)

        # We create one BSDF node per 'texture group' (Albedo slot) and mix all groups afterward.
        bsdf_nodes = {}  # type: dict[str, bpy.types.Node]
        tex_sampler_re = re.compile(r"(Main|Detail) (\d+) (Albedo|Specular|Shininess|Normal)")

        # Special case: if an Albedo map using 'UVFur' is found, we pass its alpha to ALL BSDFs.
        # TODO: Pretty sure I may want to do this for 'first group' in Elden Ring in general.
        fur_albedo_alpha = None  # type: bpy.types.NodeSocket | None

        for match, sampler in self.matdef.get_matching_samplers(tex_sampler_re, match_alias=True):
            tex_node = self.tex_image_nodes.get(sampler.alias, None)
            if tex_node and tex_node.image:
                # We only create BSDF nodes for textures that are actually used.
                bsdf_key = f"{match.group(1)} {match.group(2)}"
                map_type = match.group(3)
                try:
                    bsdf_node = bsdf_nodes[bsdf_key]
                except KeyError:
                    bsdf_node = bsdf_nodes[bsdf_key] = self.add_principled_bsdf_node(f"{bsdf_key} BSDF")

                if fur_albedo_alpha is None and sampler.uv_layer_name == "UVFur":
                    # This alpha will be used for all BSDFs.
                    fur_albedo_alpha = tex_node.outputs["Alpha"]

                if map_type == "Normal":
                    # Intervening Normal Map node required with appropriate UV layer.
                    # TODO: Some groups only have normal maps. How do I mix this? White albedo? Or `color` MATBIN param?
                    self.normal_tex_to_bsdf_node(tex_node, sampler.uv_layer_name, bsdf_node)
                else:
                    # Color multiple with lightmap, if present, and channels are split/flipped as appropriate.
                    # TODO: Main texture ALPHA should override any detail BSDF, rather than mixing with it (ER).
                    self.color_to_bsdf_node(
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

            current_last_shader = self.mix_shader_nodes(
                bsdf_nodes["Main 0"],
                bsdf_nodes["Main 1"],
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
                current_last_shader = self.mix_shader_nodes(
                    current_last_shader,
                    shader_node,
                    0.5,
                )
            else:
                # Mix all Detail BSDF nodes together using weight parameters.
                # TODO: Until I figure out the MATBIN weight parameters, just mix them all evenly.
                current_last_shader = self.mix_shader_nodes(
                    current_last_shader,
                    shader_node,
                    0.5,
                )
            current_last_shader.hide = True
            current_last_shader.location.x += i * 40.0

        if len(bsdf_nodes) == 1 and (matdef.alpha or matdef.edge):
            # Older games: mix current last shader with a Transparent BSDF using vertex alpha.
            # TODO: Does Elden Ring ever do this using an alpha blend mask?
            transparent_node = self.new("ShaderNodeBsdfTransparent", location=(self.BSDF_X, self.bsdf_y))
            # Note mix order here, so Fac 0 = fully transparent, Fac 1 = fully opaque.
            current_last_shader = self.mix_shader_nodes(
                transparent_node,
                current_last_shader,
                self.vertex_colors_nodes[0].outputs["Alpha"] if self.vertex_colors_nodes else 0.5,
            )

        self.link_to_output_surface(current_last_shader.outputs[0])  # last shader could be a BSDF or Mix Shader

        if "Displacement" in self.tex_image_nodes:
            # Texture is an actual height map (not just normals).
            disp_node = self.tex_image_nodes["Displacement"]
            # TODO: In my observation so far (DS1), this always uses UVTexture0 (i.e. never the second texture).
            self.link(self.uv_nodes["UVTexture0"].outputs["Vector"], disp_node.inputs["Vector"])
            self.link_to_output_displacement(disp_node.outputs["Color"])

        # Any BSDFs with no Albedo input use OPAQUE BLACK, not default WHITE.
        for bsdf_node in bsdf_nodes.values():
            if not bsdf_node.inputs["Base Color"].is_linked:
                bsdf_node.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)

    def color_to_bsdf_node(
        self,
        sampler: MatDefSampler,
        tex_image_node: bpy.types.Node,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
        lightmap_node: bpy.types.ShaderNodeTexImage | None = None,
        bsdf_alpha_input: bpy.types.NodeSocket | None = None,
    ):
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

        if sampler.alias.endswith("Specular"):
            # Split specular texture into specular/roughness channels.
            self.specular_tex_node_to_bsdf_principled_node(
                y=tex_image_node.location[1] - 150,  # leave room for overlay node
                color_output=color_output,
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

    def _OLD_normal_to_bsdf_node(
        self,
        tex_image_node: bpy.types.Node,
        uv_layer_name: str,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled | bpy.types.ShaderNodeBsdfDiffuse,
    ):
        """Connect given normal node (by node name) to given BSDF node, via a normal map node.

        We also need to flip the green and blue channels first.
        """
        y = tex_image_node.location[1]

        separate_color_node = self.new("ShaderNodeSeparateColor", location=(self.POST_TEX_X, y))

        green_math_node = self.new(
            "ShaderNodeMath",
            location=(self.POST_TEX_X, y - 30),
            name="Green Flip",
            label="Green Flip",
            operation="SUBTRACT",
            input_defaults={0: 1.0},
        )

        blue_math_node = self.new(
            "ShaderNodeMath",
            location=(self.POST_TEX_X, y - 60),
            name="Blue Flip",
            label="Blue Flip",
            operation="SUBTRACT",
            input_defaults={0: 1.0},
        )

        combine_color_node = self.new("ShaderNodeCombineColor", location=(self.POST_TEX_X, y - 90))

        self.link(tex_image_node.outputs["Color"], separate_color_node.inputs["Color"])
        self.link(separate_color_node.outputs["Red"], combine_color_node.inputs["Red"])
        self.link(separate_color_node.outputs["Green"], green_math_node.inputs[1])
        self.link(green_math_node.outputs["Value"], combine_color_node.inputs["Green"])
        self.link(separate_color_node.outputs["Blue"], blue_math_node.inputs[1])
        self.link(blue_math_node.outputs["Value"], combine_color_node.inputs["Blue"])

        separate_color_node.hide = True
        green_math_node.hide = True
        blue_math_node.hide = True
        combine_color_node.hide = True

        # Create normal map node.
        normal_map_node = self.add_normal_map_node(uv_layer_name, y - 120, 1.0)
        self.link(combine_color_node.outputs["Color"], normal_map_node.inputs["Color"])
        self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    def mix_shader_nodes(
        self,
        shader_0: bpy.types.Node,
        shader_1: bpy.types.Node,
        mix_fac_input: bpy.types.NodeSocket | float = 0.5,
    ) -> bpy.types.ShaderNodeMixShader:
        mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.mix_y))
        self.mix_y -= 100
        # Output 0 could be named 'BSDF' or 'Shader'.
        self.link(shader_0.outputs[0], mix_node.inputs[1])
        self.link(shader_1.outputs[0], mix_node.inputs[2])
        if isinstance(mix_fac_input, (float, int)):
            mix_node.inputs["Fac"].default_value = float(mix_fac_input)
        else:
            self.link(mix_fac_input, mix_node.inputs["Fac"])
        # noinspection PyTypeChecker
        return mix_node

    def get_bl_image(self, sampler_name: str) -> bpy.types.Image | None:
        """All Blender Images from textures (cached or DDS) are lower-case names. FLVER paths are not case-sensitive."""
        texture_stem = self.sampler_texture_stems[sampler_name].lower()
        if not texture_stem:
            # No texture given in MATBIN or FLVER.
            return None
        # Search for Blender image with no extension, TGA, PNG, or DDS, in that order of preference.
        for image_name in (f"{texture_stem}", f"{texture_stem}.tga", f"{texture_stem}.png", f"{texture_stem}.dds"):
            try:
                return bpy.data.images[image_name]
            except KeyError:
                pass
        else:
            # Blender image not found. Create empty 1x1 Blender image.
            bl_image = bpy.data.images.new(name=texture_stem, width=1, height=1, alpha=True)
            bl_image.pixels = [1.0, 0.0, 1.0, 1.0]  # magenta
            if self.context.scene.flver_import_settings.import_textures:  # otherwise, expected to be missing
                self.operator.warning(
                    f"Could not find texture '{texture_stem}' in Blender image data. Created 1x1 magenta Image."
                )
            return bl_image

    # region Texture Input Methods

    def specular_tex_node_to_bsdf_principled_node(
        self,
        y: float,
        color_output: bpy.types.NodeSocket,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
        is_metallic=False,
    ):
        """Split color channels of a specular texture into Principled BSDF inputs."""

        group_node = self.tree.nodes.new('ShaderNodeGroup')
        group_key = "Process Specular"
        if is_metallic:
            group_key += " (Metallic)"
        group_node.node_tree = bpy.data.node_groups[group_key]
        group_node.name = group_node.label = "Process Specular"

        group_node.location = (self.POST_TEX_X, y)

        # Link texture color to processing group input.
        self.link(color_output, group_node.inputs["Color In"])

        # Link normal map output to BSDF node Normal.
        if is_metallic:
            self.link(group_node.outputs["Metallic"], bsdf_node.inputs["Metallic"])
        else:
            self.link(group_node.outputs["Specular IOR Level"], bsdf_node.inputs["Specular IOR Level"])
        self.link(group_node.outputs["Roughness"], bsdf_node.inputs["Roughness"])
        self.link(group_node.outputs["Transmission Weight"], bsdf_node.inputs["Transmission Weight"])

    def normal_tex_to_bsdf_node(
        self,
        image_tex_node: bpy.types.ShaderNodeTexImage,
        uv_layer_name: str,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled | bpy.types.ShaderNodeBsdfDiffuse,
    ):
        """Create a node group that processes input normal map colors (for given game) to Blender normal colors.

        Blender expects red to be the X component (right positive), green to be the Y component (up positive), and blue
        to be the Z component. It also expects the color range [0, 1] to actually represent the normal range [-1, 1],
        i.e. uses a full spherical mapping.

        FromSoft game maps use a hemispherical mapping (all normals are convex), omit Z (normalized vectors), variably
        use G (earlier games) vs. B (later games) for the Y component, and invert their Y component, all of which we
        handle here.

        NOTE: Currently assuming that DeS and DS1:PTDE use red/blue maps, and all other games use red/green maps.
        """
        y = image_tex_node.location[1]
        color_output = image_tex_node.outputs["Color"]

        settings = self.context.scene.soulstruct_settings

        group_node = self.tree.nodes.new('ShaderNodeGroup')
        group_key = "Process RB Normal" if settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE) else "Process RG Normal"
        group_node.node_tree = bpy.data.node_groups[group_key]
        group_node.name = group_node.label = "Process Normals"

        group_node.location = (self.POST_TEX_X, y)

        # Link texture color to processing group input.
        self.link(color_output, group_node.inputs["Color In"])

        # Create normal map node and link processing group output to it.
        normal_map_node = self.add_normal_map_node(uv_layer_name, y - 120, 1.0)
        self.link(group_node.outputs["Normal Out"], normal_map_node.inputs["Color"])

        # Link normal map output to BSDF node Normal.
        self.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

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
        return _new_node(self.tree, node_type, location, input_defaults=input_defaults, **kwargs)

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

    def add_tex_image_node(
        self, name: str, image: bpy.types.Image | None, label: str = None, hide=False
    ) -> bpy.types.ShaderNodeTexImage:
        node = self.new(
            "ShaderNodeTexImage",
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

    def add_principled_bsdf_node(self, bsdf_name: str, label: str = "") -> bpy.types.ShaderNodeBsdfPrincipled:
        node = self.new(
            "ShaderNodeBsdfPrincipled",
            location=(self.BSDF_X, self.bsdf_y),
            name=bsdf_name,
            input_defaults={"Roughness": 0.75},
            label=label or bsdf_name,
        )
        self.bsdf_y -= 1000
        # noinspection PyTypeChecker
        return node

    def add_normal_map_node(self, uv_map_name: str, location_y: float, strength=1.0) -> bpy.types.ShaderNodeNormalMap:
        # noinspection PyTypeChecker
        return self.new(
            "ShaderNodeNormalMap",
            location=(self.POST_TEX_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": strength},
        )

    # endregion


def create_node_groups():
    """One-off function for creating node groups for game-specific normal processing."""

    if "Process Specular" not in bpy.data.node_groups:
        group = bpy.data.node_groups.new("Process Specular", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_specular_processing_node_group(group, is_metallic=False)

    if "Process Specular (Metallic)" not in bpy.data.node_groups:
        group = bpy.data.node_groups.new("Process Specular (Metallic)", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_specular_processing_node_group(group, is_metallic=True)

    if "Process RG Normal" not in bpy.data.node_groups:
        group = bpy.data.node_groups.new("Process RG Normal", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_normal_processing_node_group_tree(group, uses_green=True)

    if "Process RB Normal" not in bpy.data.node_groups:
        group = bpy.data.node_groups.new("Process RB Normal", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_normal_processing_node_group_tree(group, uses_green=False)


def _build_specular_processing_node_group(tree: bpy.types.NodeTree, is_metallic: bool):

    # Create input/output sockets for group.
    tree.interface.new_socket(
        name="Color In", description="Specular Map Texture Color Input", in_out="INPUT", socket_type="NodeSocketColor"
    )
    if is_metallic:
        tree.interface.new_socket(
            name="Metallic", description="Metallic strength", in_out="OUTPUT", socket_type="NodeSocketFloat"
        )
    else:
        tree.interface.new_socket(
            name="Specular IOR Level", description="Specular IOR level", in_out="OUTPUT", socket_type="NodeSocketFloat"
        )
    tree.interface.new_socket(
        name="Roughness", description="Specular roughness", in_out="OUTPUT", socket_type="NodeSocketFloat"
    )
    tree.interface.new_socket(
        name="Transmission Weight", description="Specular transmission", in_out="OUTPUT", socket_type="NodeSocketFloat"
    )

    # Create nodes for group input and output.
    group_in = tree.nodes.new('NodeGroupInput')
    group_in.location = (-400, 0)

    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (200, 0)

    # Separate the incoming color into R, G, B.
    sep_rgb = tree.nodes.new('ShaderNodeSeparateRGB')
    sep_rgb.location = (-200, 0)
    tree.links.new(group_in.outputs["Color In"], sep_rgb.inputs[0])

    red_flip = _new_math_node(tree, "SUBTRACT", (0, 150), 1.0, sep_rgb.outputs["R"])
    red_flip.name = red_flip.label = "Red Flip"
    green_flip = _new_math_node(tree, "SUBTRACT", (0, 0), 1.0, sep_rgb.outputs["G"])
    green_flip.name = green_flip.label = "Green Flip"

    tree.links.new(red_flip.outputs[0], group_out.inputs["Metallic" if is_metallic else "Specular IOR Level"])
    tree.links.new(green_flip.outputs[0], group_out.inputs["Roughness"])
    tree.links.new(sep_rgb.outputs["B"], group_out.inputs["Transmission Weight"])  # not flipped


def _build_normal_processing_node_group_tree(tree: bpy.types.NodeTree, uses_green: bool):

    # Create input/output sockets for group.
    tree.interface.new_socket(
        name="Color In", description="Normal Map Texture Color Input", in_out="INPUT", socket_type="NodeSocketColor"
    )
    tree.interface.new_socket(
        name="Normal Out", description="Normal Map Color Output", in_out="OUTPUT", socket_type="NodeSocketColor"
    )

    r_height = 200
    flipped_height = 0 if uses_green else -200
    computed_height = -200 if uses_green else 0

    # Create nodes for group input and output.
    group_in = tree.nodes.new('NodeGroupInput')
    group_in.location = (-400, 0)

    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (2200, 0)

    # Separate the incoming color into R, G, B.
    sep_rgb = tree.nodes.new('ShaderNodeSeparateRGB')
    sep_rgb.location = (-200, 0)
    tree.links.new(group_in.outputs["Color In"], sep_rgb.inputs[0])

    # Process the Red channel (X):
    #    X_temp = 2*R - 1
    mult_r = _new_math_node(tree, "MULTIPLY", (0, r_height), input_0=sep_rgb.outputs["R"], input_1=2.0)
    sub_r = _new_math_node(tree, "SUBTRACT", (200, r_height), input_0=mult_r.outputs[0], input_1=1.0)
    # sub_r output is X in [-1,1].

    # Process the Green/Blue channel:
    #    First flip: G' = 1 - G
    flip_g_or_b = _new_math_node(
        tree, "SUBTRACT", (0, flipped_height), 1.0, sep_rgb.outputs["G" if uses_green else "B"]
    )
    flip_g_or_b.label = "Flip"
    #    Then convert to [-1,1]: Y = 2*G' - 1
    mult_g_or_b = _new_math_node(tree, "MULTIPLY", (200, flipped_height), flip_g_or_b.outputs[0], 2.0)
    sub_g_or_b = _new_math_node(tree, "SUBTRACT", (400, flipped_height), mult_g_or_b.outputs[0], 1.0)

    # Compute X^2 and Y^2.
    x_squared = _new_math_node(tree, "POWER", (600, r_height), sub_r.outputs[0], 2.0)
    y_squared = _new_math_node(tree, "POWER", (600, flipped_height), sub_g_or_b.outputs[0], 2.0)

    # Sum X^2 and Y^2.
    sum_of_squares = _new_math_node(tree, "ADD", (800, computed_height), x_squared.outputs[0], y_squared.outputs[0])

    # Compute Z^2 = 1 - (X^2 + Y^2).
    z_squared = _new_math_node(tree, "SUBTRACT", (1000, computed_height), 1.0, sum_of_squares.outputs[0])

    # Clamp to ensure non-negative, then compute Z = sqrt(1 - X^2 - Y^2).
    z_squared_clamped = _new_math_node(tree, "MAXIMUM", (1200, computed_height), z_squared.outputs[0], 0.0)
    z = _new_math_node(tree, "SQRT", (1400, computed_height), z_squared_clamped.outputs[0])
    # `z` output is Z in [0,1] (since our input is hemispherical, Z is always positive).

    # Remap computed components back to [0,1] for Blender's Normal Map node:
    #    Remap function: Out = (component + 1) / 2

    add_x = _new_math_node(tree, "ADD", (1600, 200), sub_r.outputs[0], 1.0)
    output_r = _new_math_node(tree, "MULTIPLY", (1800, 200), add_x.outputs[0], 0.5)
    add_y = _new_math_node(tree, "ADD", (1600, 0), sub_g_or_b.outputs[0], 1.0)
    output_g_or_b = _new_math_node(tree, "MULTIPLY", (1800, 0), add_y.outputs[0], 0.5)
    add_z = _new_math_node(tree, "ADD", (1600, -200), z.outputs[0], 1.0)
    output_b_or_g = _new_math_node(tree, "MULTIPLY", (1800, -200), add_z.outputs[0], 0.5)

    # Recombine the remapped channels into one vector.
    combine_rgb = tree.nodes.new('ShaderNodeCombineRGB')
    combine_rgb.location = (2000, 0)
    tree.links.new(output_r.outputs[0], combine_rgb.inputs['R'])
    if uses_green:
        tree.links.new(output_g_or_b.outputs[0], combine_rgb.inputs['G'])  # flipped
        tree.links.new(output_b_or_g.outputs[0], combine_rgb.inputs['B'])  # computed
    else:
        tree.links.new(output_b_or_g.outputs[0], combine_rgb.inputs['G'])  # computed
        tree.links.new(output_g_or_b.outputs[0], combine_rgb.inputs['B'])  # flipped

    # Output the resulting normal.
    tree.links.new(combine_rgb.outputs[0], group_out.inputs["Normal Out"])


def _new_node(
    tree: bpy.types.NodeTree,
    node_type: str,
    location: tuple[int, int] = None,
    /,
    input_defaults: dict[str | int, tp.Any] = None,
    **kwargs,
) -> bpy.types.Node:
    node = tree.nodes.new(node_type)
    if location is not None:
        node.location = location
    for k, v in kwargs.items():
        setattr(node, k, v)
    if input_defaults:
        for k, v in input_defaults.items():
            node.inputs[k].default_value = v
    return node


def _new_math_node(
    tree: bpy.types.NodeTree,
    operation: str,
    location: tuple[int, int],
    input_0: float | bpy.types.NodeSocket = None,
    input_1: float | bpy.types.NodeSocket = None,
) -> bpy.types.ShaderNodeMath:
    node = tree.nodes.new('ShaderNodeMath')
    node.operation = operation
    node.location = location

    if isinstance(input_0, bpy.types.NodeSocket):
        tree.links.new(input_0, node.inputs[0])
    elif input_0 is not None:
        node.inputs[0].default_value = input_0

    if isinstance(input_1, bpy.types.NodeSocket):
        tree.links.new(input_1, node.inputs[1])
    elif input_1 is not None:
        node.inputs[1].default_value = input_1

    # noinspection PyTypeChecker
    return node
