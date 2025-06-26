from __future__ import annotations

__all__ = [
    "NodeTreeBuilder_DS1R",
]

from dataclasses import dataclass

import bpy
from bpy.types import NodeSocket

from .base_node_tree_builder import NodeTreeBuilder
from .utilities import TEX_SAMPLER_RE


@dataclass(slots=True)
class NodeTreeBuilder_DS1R(NodeTreeBuilder):
    """Node tree builder for Dark Souls: Remastered.
    
    Thanks to @thegreatgramcracker for implementing the pre-baked node groups and build logic for DS1R.
    """

    @property
    def _diffuse_map_color(self) -> tuple[float, ...]:
        """Get RGBA diffuse map color. Defaults to (1, 1, 1, 1)."""
        return tuple(float(x) for x in self.get_mtd_param("g_DiffuseMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _specular_map_color(self):
        return tuple(float(x) for x in self.get_mtd_param("g_SpecularMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    def _build_shader(self):
        if "FRPG_Phn_ColDif" in self.matdef.shader_stem:

            if self.get_mtd_param("g_LightingType", default=1) == 0:
                # If `g_LightingType == 0`, nothing matters but the final surface image.
                # This shader is probably fine for all games, but should be verified.
                self._build_ds1r_diffuse_no_light_shader("Generic Diffuse No Light")
                return

            if self.get_mtd_param("g_MaterialWorkflow", default=0) == 1:
                # Using legacy specular workflow with added roughness in the alpha channel.
                self._build_ds1r_shader(node_group_name="DS1R Basic Colored Spec")
                return

            # Regular PBR workflow.
            self._build_ds1r_shader(node_group_name="DS1R Basic PBR")
            return

        if self.matdef.shader_category == "NormalToAlpha":
            # Used by fog, lightshafts, and some tree leaves. Fades out the object when viewed side-on.
            self._build_ds1r_normal_to_alpha_shader()
            return
        
        # Fall back to base catch-all shader.
        super(NodeTreeBuilder_DS1R, self)._build_shader()
        return

    def _build_ds1r_shader(self, node_group_name: str = "DS1R Basic PBR"):
        """Builds the common surface shaders for DS1R.
        
        Might be expanded/repurposed to build node group shaders from other games depending on how different they are.

        TODO: Implement UV scroll and parallax occlusion mapping. These should probably happen outside the node group,
         similar to UV Scale, since they just modify the UVs.

        Shader references:
            https://github.com/AltimorTASDK/dsr-shader-mods
            https://github.com/magcius/noclip.website/blob/main/src/DarkSouls/render.ts
            StaydMcMuffin
        """
        node_groups = {}  # type: dict[str, bpy.types.ShaderNodeGroup]
        mix_fac_input = 0.5
        
        detail_output_socket = self._get_detail_output_socket()
        lightmap_node = self.tex_image_nodes.get("g_Lightmap", None)

        def _create_node_group():
            # TODO: Currently doesn't handle case of invalid `node_group_name` (not in packaged Blend file).
            node_group_inputs = {}
            if lightmap_node is not None:
                # Link lightmap node to each new node group. This is probably not accurate for lightmap display
                # but at least it gives some approximation. TODO: gram working on an Emissive group for this?
                node_group_inputs["Light Map Influence"] = 0.5
                node_group_inputs["Light Map"] = lightmap_node.outputs["Color"]
            if self.vertex_colors_nodes:
                # Link vertex colors to each new node group.
                node_group_inputs["Vertex Colors"] = self.vertex_colors_nodes[0].outputs["Color"]

            node_groups[node_group_key] = self._new_bsdf_shader_node_group(node_group_name, inputs=node_group_inputs)
            return node_groups[node_group_key]

        for match, sampler in self.matdef.get_matching_samplers(TEX_SAMPLER_RE, match_alias=True):
            node_group_key = f"{match.group(2)}"  # '0', '1', '2', ...
            tex_node = self.tex_image_nodes.get(sampler.alias, None)
            
            if tex_node and tex_node.image:  # TODO: Do we not want to connect this up if Image is unassigned?
                map_type = match.group(3)
                if node_group_key in node_groups:
                    node_group = node_groups[node_group_key]
                else:
                    node_group = _create_node_group()

                if map_type == "Albedo":
                    # This could be changed to linear (non-color) space, since the shaders use it as linear for all
                    # calculations, then transforms it to sRGB at the very end using x^2.2
                    self.link(tex_node.outputs["Color"], node_group.inputs["Diffuse Map"])
                    node_group.inputs["Diffuse Map Color"].default_value = self._diffuse_map_color
                    node_group.inputs["Diffuse Map Color Power"].default_value = self.get_mtd_param(
                        "g_DiffuseMapColorPower", default=1
                    )
                    if self.matdef.edge or self.matdef.alpha:
                        self.link(tex_node.outputs["Alpha"], node_group.inputs["Diffuse Map Alpha"])

                if map_type == "Normal":
                    _, normal_map_node = self._normal_tex_to_normal_input(
                        y=tex_node.location[1],
                        color_input_from=tex_node.outputs["Color"],
                        normal_output_to=node_group.inputs["Normal"],
                        uv_layer_name=sampler.uv_layer_name,
                    )
                    if detail_output_socket and self.get_mtd_param("g_DetailBump_BumpPower", default=0) > 0:
                        # Create an add vector node for this and the detail bumpmap, then link that to the node group
                        combine_detail_node = self._new_normal_combine_node(
                            node_y=tex_node.location[1] - 150,
                            inputs={0: normal_map_node.outputs["Normal"], 1: detail_output_socket},
                            outputs={0: node_group.inputs["Normal"]},  # will replace the normal map input above
                        )
                        combine_detail_node.hide = True

                if map_type == "Specular":
                    self.link(tex_node.outputs["Color"], node_group.inputs["Specular Map"])
                    self.link(tex_node.outputs["Alpha"], node_group.inputs["Specular Map Alpha"])
                    node_group.inputs["Specular Map Color"].default_value = self._specular_map_color
                    node_group.inputs["Specular Map Color Power"].default_value = self.get_mtd_param(
                        "g_SpecularMapColorPower", default=1
                    )

        if self.vertex_colors_nodes:
            mix_fac_input = self.vertex_colors_nodes[0].outputs["Alpha"]

        # NOTE: No 3-group setup to handle in DS1R (snow shader handled separately).
        if len(node_groups) == 2:
            # TODO: Should probably mix each sampler pair of texture maps rather than mixing two BSDFs.
            mix_node = self._mix_shader_nodes(
                node_groups["0"].outputs[0],
                node_groups["1"].outputs[0],
                mix_fac_input,
            )
            self.link(mix_node.outputs[0], self.output_surface)
        elif len(node_groups) == 1:
            out_node = node_groups["0"]
            if self.matdef.edge or self.matdef.alpha:
                self.link(self.vertex_colors_nodes[0].outputs["Alpha"], out_node.inputs["Vertex Colors Alpha"])
            self.link(out_node.outputs[0], self.output_surface)

    def _build_ds1r_diffuse_no_light_shader(self, node_group_name: str) -> bpy.types.ShaderNodeGroup:
        """This shader is used for objects that don't receive lighting, like the skybox.

        TODO: Probably generic enough to be used with other games.
        """
        diffuse_node = self.tex_image_nodes.get("Main 0 Albedo")
        shader_inputs = {
            "Diffuse Map": diffuse_node.outputs["Color"],
            "Diffuse Map Color": self._diffuse_map_color,
            "Diffuse Map Color Power": self.get_mtd_param("g_DiffuseMapColorPower", default=1),
        }
        if self.matdef.edge or self.matdef.alpha:
            shader_inputs["Diffuse Map Alpha"] = diffuse_node.outputs["Alpha"]
        if len(self.vertex_colors_nodes) > 0:
            shader_inputs["Vertex Colors"] = self.vertex_colors_nodes[0].outputs["Color"]
            shader_inputs["Vertex Colors Alpha"] = self.vertex_colors_nodes[0].outputs["Alpha"]

        return self._new_bsdf_shader_node_group(
            node_group_name,
            inputs=shader_inputs,
            outputs={0: self.output_surface},
        )

    def _build_ds1r_normal_to_alpha_shader(self) -> bpy.types.ShaderNodeGroup:
        """Same as the diffuse no-light shader, but also fades out the object past certain viewing angles."""
        node_group = self._build_ds1r_diffuse_no_light_shader("DS1R Normal to Alpha")
        node_group.inputs["Min Angle"].default_value = self.get_mtd_param("g_Normal2Alpha_MinAngle", default=90)
        node_group.inputs["Max Angle"].default_value = self.get_mtd_param("g_Normal2Alpha_MaxAngle", default=80)
        return node_group

    def _get_detail_output_socket(self) -> NodeSocket | None:
        detail_node = self.tex_image_nodes.get("Detail 0 Normal", None)
        if not detail_node:
            return None

        _, normal_map_node = self._normal_tex_to_normal_input(
            y=detail_node.location[1],
            color_input_from=detail_node.outputs["Color"],
            normal_output_to=None,  # assigned by caller to all texture node groups
            uv_layer_name="UVTexture0",  # always UVTexture0 for detail maps
        )
        return normal_map_node.outputs["Normal"]
