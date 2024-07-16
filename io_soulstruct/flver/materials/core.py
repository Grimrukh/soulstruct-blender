from __future__ import annotations

__all__ = [
    "MaterialCreationError",
    "create_submesh_blender_material",
]

import re
import typing as tp
from dataclasses import dataclass, field

import bpy

from soulstruct.base.models.flver.material import Material
from soulstruct.base.models.shaders import MatDef, MatDefSampler
from soulstruct.base.models.flver.submesh import Submesh
from soulstruct.utilities.maths import Vector2

from io_soulstruct.utilities.operators import LoggingOperator

# Main node input for specular strength is called "Specular IOR Level" in Blender 4.X, but "Specular" prior to that.
if bpy.app.version[0] == 4:
    PRINCIPLED_SPECULAR_INPUT = "Specular IOR Level"
    PRINCIPLED_SHININESS_INPUT = "Sheen Weight"
    PRINCIPLED_TRANSMISSION_INPUT = "Transmission Weight"
else:
    PRINCIPLED_SPECULAR_INPUT = "Specular"
    PRINCIPLED_SHININESS_INPUT = "Sheen"
    PRINCIPLED_TRANSMISSION_INPUT = "Transmission"


class MaterialCreationError(Exception):
    """Error raised during material shader creation. Generally non-fatal, as the critical texture nodes required for
    export are typically easy to create. This just means a more faithful shader couldn't be built."""


def create_submesh_blender_material(
    operator: LoggingOperator,
    material: Material,
    flver_sampler_texture_stems: dict[str, str],
    material_name: str,
    matdef: MatDef | None,
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
        if matdef and matdef.edge:
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
    #  games, but probably not for, say, Elden Ring map pieces. Some kind of auto-decimator may be in order.
    bl_material["Face Set Count"] = len(submesh.face_sets)
    bl_material.use_backface_culling = submesh.use_backface_culling

    # Store GX items as custom properties 'array', except the final dummy item.
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

    if not matdef:
        # Store FLVER sampler texture paths directly in custom properties. No shader tree will be built, but at least
        # we can faithfully write FLVER texture paths back to files on export.
        for sampler_name, texture_stem in flver_sampler_texture_stems.items():
            bl_material[f"Path[{sampler_name}]"] = texture_stem
        return bl_material

    # Retrieve any texture paths given from the MATBIN.
    sampler_texture_stems = {sampler.name: sampler.matbin_texture_stem for sampler in matdef.samplers}

    # Apply FLVER overrides to texture paths.
    found_sampler_names = set()
    for sampler_name, texture_stem in flver_sampler_texture_stems.items():

        if sampler_name in found_sampler_names:
            operator.warning(
                f"Texture for sampler '{sampler_name}' was given multiple times in FLVER material, which is "
                f"invalid. Please repair this corrupt FLVER file. Ignoring this duplicate texture instance.",
            )
            continue
        found_sampler_names.add(sampler_name)

        if sampler_name not in sampler_texture_stems:
            # Unexpected sampler name!
            if warn_missing_textures:
                operator.warning(
                    f"Sampler '{sampler_name}' given in FLVER does not seem to be supported by material definition "
                    f"'{matdef.name}' with shader '{matdef.shader_stem}'. Texture node will be created, but with no UV "
                    f"layer input.",
                )
            sampler_texture_stems[sampler_name] = texture_stem
            continue

        if not texture_stem:
            # No override given in FLVER. Rare in games that use MTD, but still happens, and very common in later
            # MATBIN games with super-flexible billion-sampler shaders.
            continue

        # Override texture path.
        sampler_texture_stems[sampler_name] = texture_stem

    # Try to build shader nodetree.
    try:
        builder = NodeTreeBuilder(
            operator=operator,
            material=bl_material,
            matdef=matdef,
            sampler_texture_stems=sampler_texture_stems,
            vertex_color_count=vertex_color_count,
        )
        builder.build()
    except (MaterialCreationError, KeyError, ValueError, IndexError) as ex:
        operator.warning(
            f"Error building shader for material '{material_name}'. Textures written to custom properties. Error:\n"
            f"    {ex}")
        for sampler_name, texture_stem in flver_sampler_texture_stems.items():
            bl_material[f"Path[{sampler_name}]"] = texture_stem
        return bl_material

    return bl_material


@dataclass(slots=True)
class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials."""

    operator: LoggingOperator
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
    # Maps common, non-game-specific sampler type (e.g. 'ALBEDO_0') to Nodes.
    tex_image_nodes: dict[str, bpy.types.Node] = field(default_factory=dict)

    tree: bpy.types.NodeTree = field(init=False)
    output: bpy.types.Node = field(init=False)

    # X coordinates of node type columns.
    VERTEX_COLORS_X: tp.ClassVar[int] = -950
    UV_X: tp.ClassVar[int] = -950
    SCALE_X: tp.ClassVar[int] = -750
    TEX_X: tp.ClassVar[int] = -550
    POST_TEX_X: tp.ClassVar[int] = -250  # overlay, split, math, etc.
    BSDF_X: tp.ClassVar[int] = -50
    MIX_X: tp.ClassVar[int] = 100

    def __post_init__(self):
        self.tree = self.material.node_tree
        self.output = self.tree.nodes["Material Output"]

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
            raise MaterialCreationError(
                f"Could not build UV coordinate nodes for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )

        try:
            if self.matdef.is_water:
                self.build_water_shader()
                return
            elif self.matdef.is_snow:  # TODO: I used to check texture count was 1 here.
                self.build_snow_shader()
                return
        except MaterialCreationError as ex:
            self.operator.warning(
                f"Error building special shader for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )
            return

        # Build game-dependent or generic shader.
        try:
            self.build_standard_shader(self.matdef)
        except MaterialCreationError as ex:
            self.operator.warning(
                f"Error building shader for material '{self.matdef.name}' with shader '{self.matdef.shader_stem}'. "
                f"Error:\n    {ex}"
            )

    def build_shader_uv_texture_nodes(self):
        """Build UV and texture nodes. Used by all games."""

        self.uv_nodes = {}
        self.tex_image_nodes = {}  # type: dict[str, bpy.types.Node]
        uv_scale_nodes = {}

        # We add Image Texture nodes in `MatDef` order, not FLVER order.
        # This is because in later games, MatDef samplers are already nicely grouped together from metaparam.

        current_sampler_group = self.matdef.samplers[0].sampler_group
        for sampler in self.matdef.samplers:

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
            tex_image_node = self.add_tex_image_node(node_name, image=bl_image, label=node_label, hide=bl_image is None)

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
                sampler_name, image=bl_image, label=sampler_name, hide=bl_image is None
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
            raise MaterialCreationError(
                "This `MatDef` game subclass does not define 'UVTexture0' layer, which is required for water shader."
            )

        normal_map_node = self.add_normal_map_node(uv_texture_0, normal_node.location[1])
        self.link(normal_node.outputs["Color"], normal_map_node.inputs["Color"])
        self.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
        self.link(self.vertex_colors_nodes[0].outputs["Alpha"], water_mix.inputs["Fac"])
        return True

    def build_snow_shader(self):
        """
        Sketch for DS1R snow shader:
         - Mix a standard Principled BSDF (main texture, e.g. ground) and a Diffuse BSDF shader for snow.
         - Use 'ALBEDO_0' and 'METALLIC_0' as usual for Principled.
             - Mix 'LIGHTMAP' as overlay if present.
         - Snow diffuse uses both 'NORMAL_0' (which is sometimes a diffuse snow texture!) and 'NORMAL_1' as
           its BSDF normal input (mapped with UVTexture0). We mix these two textures 50/50 if given.
         - 'NORMAL_2' is actually the normal map for the Principled BSDF, but only appears in DS1R! Not PTDE.
          TODO: Double check that it's not *NORMAL_1* (detailed bumpmap) that is missing in PTDE.
         - Mix shader nodes using vertex color alpha, raised with a Math node to the power of 4.0, which seems to
           capture the snow effect best in my tuning.
         - Create a Mix Shader for the standard textures and new Diffuse snow BSDF. Plug into material output.
        """

        bsdf_node = self.add_principled_bsdf_node("Main 0 BSDF")
        diffuse_bsdf_node = self.new("ShaderNodeBsdfDiffuse", location=(self.BSDF_X, self.bsdf_y))
        self.bsdf_y -= 1000

        # Mix Principled BSDF 0 with snow diffuse.
        mix_node = self.new("ShaderNodeMixShader", location=(self.MIX_X, self.mix_y))
        self.link(bsdf_node.outputs["BSDF"], mix_node.inputs[1])
        self.link(diffuse_bsdf_node.outputs["BSDF"], mix_node.inputs[2])

        # Raise vertex alpha to the power of 4.0 and use as mix Fac.
        vertex_alpha_power = self.new(
            "ShaderNodeMath", location=(self.BSDF_X, self.mix_y), operation="POWER", input_defaults={1: 4.0}
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
        self.normal_to_bsdf_node(self.tex_image_nodes["Main 1 Normal"], "UVTexture0", diffuse_bsdf_node)

        if "Main 2 Normal" in self.tex_image_nodes:
            # Only known use of 'Main 2 Normal' in DS1R, and it's the normal map of the main texture (e.g. ground).
            self.normal_to_bsdf_node(self.tex_image_nodes["Main 2 Normal"], "UVTexture0", bsdf_node)

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
                    self.normal_to_bsdf_node(tex_node, sampler.uv_layer_name, bsdf_node)
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
            self.specular_to_principled(
                tex_image_node.location[1],
                color_output,
                bsdf_node,
                is_metallic="Metallic" in sampler.name,  # different setup for later games
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
            self.link(color_output, bsdf_node.inputs[PRINCIPLED_SHININESS_INPUT])

    def normal_to_bsdf_node(
        self,
        tex_image_node: bpy.types.Node,
        uv_layer_name: str,
        bsdf_node: bpy.types.ShaderNodeBsdfPrincipled,
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
        return mix_node

    def get_bl_image(self, sampler_name: str) -> bpy.types.Image | None:
        texture_stem = self.sampler_texture_stems[sampler_name]
        if not texture_stem:
            # No texture given in MATBIN or FLVER.
            return None
        # Search for Blender image with no extension, PNG, or DDS, in that order of preference.
        for image_name in (f"{texture_stem}", f"{texture_stem}.png", f"{texture_stem}.dds"):
            if image_name in bpy.data.images:
                return bpy.data.images[image_name]
        else:
            # Blender image not found. Create empty 1x1 Blender image.
            bl_image = bpy.data.images.new(name=texture_stem, width=1, height=1, alpha=True)
            bl_image.pixels = [1.0, 0.0, 1.0, 1.0]  # magenta
            self.operator.warning(
                f"Could not find texture '{texture_stem}' (no extension, PNG, or DDS) in Blender image data. "
                f"Created 1x1 magenta texture for node."
            )
            return bl_image

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
            location=(self.POST_TEX_X, y - 40),
            name="Red Flip",
            label="Red Flip",
            operation="SUBTRACT",
            input_defaults={0: 1.0},
        )
        green_math_node = self.new(
            "ShaderNodeMath",
            location=(self.POST_TEX_X, y - 80),
            name="Green Flip",
            label="Green Flip",
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

        separate_color_node.hide = True
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

    def add_tex_image_node(self, name: str, image: bpy.types.Image | None, label: str = None, hide=False):
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
        return node

    def add_principled_bsdf_node(self, bsdf_name: str, label: str = ""):
        node = self.new(
            "ShaderNodeBsdfPrincipled",
            location=(self.BSDF_X, self.bsdf_y),
            name=bsdf_name,
            input_defaults={"Roughness": 0.75},
            label=label or bsdf_name,
        )
        self.bsdf_y -= 1000
        return node

    def add_normal_map_node(self, uv_map_name: str, location_y: float, strength=1.0):
        return self.new(
            "ShaderNodeNormalMap",
            location=(self.POST_TEX_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": strength},
        )

    # endregion
