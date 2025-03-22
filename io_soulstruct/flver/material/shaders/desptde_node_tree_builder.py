from __future__ import annotations

__all__ = [
    "NodeTreeBuilder_DESPTDE",
]

from dataclasses import dataclass

import bpy
from bpy.types import NodeSocket

from .base_node_tree_builder import NodeTreeBuilder
from .utilities import TEX_SAMPLER_RE


@dataclass(slots=True)
class NodeTreeBuilder_DESPTDE(NodeTreeBuilder):
    """Node tree builder for Dark Souls: Prepare to Die Edition and Demon's Souls.

    Thanks to @thegreatgramcracker for implementing the pre-baked node groups and build logic.
    """

    @property
    def _diffuse_map_color(self) -> tuple[float, ...]:
        """Get RGBA diffuse map color. Defaults to (1, 1, 1, 1)."""
        return tuple(float(x) for x in self.get_mtd_param("g_DiffuseMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _specular_map_color(self):
        return tuple(float(x) for x in self.get_mtd_param("g_SpecularMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _specular_power(self) -> float:
        """Blinn-phong specularity"""
        return self.get_mtd_param("g_SpecularPower", default=2)

    def _build_shader(self):
        if "_Phn_ColDif" in self.matdef.shader_stem:
            if self.get_mtd_param("g_LightingType", default=1) == 0:
                # This i
                self._build_diffuse_only_shader("Generic Diffuse Only")
                return
            self._build_desptde_shader(node_group_name="DeS/PTDE Basic Shader")
            return
        if self.matdef.shader_category == "NormalToAlpha":
            # Used by fog, lightshafts, and some tree leaves. Fades out the object when viewed side-on.
            self._build_ds1_normal_to_alpha_shader()
            return
        # Fall back to base catch-all shader.
        super(NodeTreeBuilder_DESPTDE, self)._build_shader()
        return

    def _build_desptde_shader(self, node_group_name: str = "DeS/PTDE Basic Shader"):
        """Builds the common surface shaders for DeS and DS1 PTDE.

           Shader model for these games is Blinn-phong, which is not supported in Blender,
           but these shaders can do at least some approximation.
        """
        node_groups = {}  # type: dict[str, bpy.types.ShaderNodeGroup]
        mix_fac_input = 0.5
        
        detail_output_socket = self._get_detail_output_socket()
        lightmap_node = self.tex_image_nodes.get("Lightmap", None)

        def _create_node_group():
            # TODO: Currently doesn't handle case of invalid `node_group_name` (not in packaged Blend file).
            node_group_inputs = {}
            if lightmap_node is not None:
                # Link lightmap node to each new node group.
                node_group_inputs["Light Map Influence"] = 1
                node_group_inputs["Light Map"] = lightmap_node.outputs["Color"]
            if self.vertex_colors_nodes:
                # Link vertex colors to each new node group.
                node_group_inputs["Vertex Colors"] = self.vertex_colors_nodes[0].outputs["Color"]
            node_group_inputs["Specular Power"] = self._specular_power

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
                    node_group.inputs["Specular Map Color"].default_value = self._specular_map_color
                    node_group.inputs["Specular Map Color Power"].default_value = self.get_mtd_param(
                        "g_SpecularMapColorPower", default=1
                    )

        if self.vertex_colors_nodes:
            mix_fac_input = self.vertex_colors_nodes[0].outputs["Alpha"]

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


    def _build_diffuse_only_shader(self, node_group_name: str) -> bpy.types.ShaderNodeGroup:
        """This shader is used for objects that only use diffuse, and for lighting type = 0 objects.
            Lighting type 0 can't be accurately represented in Blender since it's behaviour is that
            it receives color from the draw params, but no light from point lights.

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

    def _build_ds1_normal_to_alpha_shader(self) -> bpy.types.ShaderNodeGroup:
        """Same as the diffuse no-light shader, but also fades out the object past certain viewing angles."""
        node_group = self._build_diffuse_only_shader("DS1 Normal to Alpha")
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
