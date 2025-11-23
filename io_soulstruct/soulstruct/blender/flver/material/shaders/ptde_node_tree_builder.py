from __future__ import annotations

__all__ = [
    "NodeTreeBuilder_PTDE",
]

import re
from dataclasses import dataclass

import bpy
from bpy.types import NodeSocket
from soulstruct.utilities.maths import Vector2

from .base_node_tree_builder import NodeTreeBuilder
from .node_tree import new_shader_node
from soulstruct.blender.exceptions import MaterialImportError
from .utilities import TEX_SAMPLER_RE


@dataclass(slots=True)
class NodeTreeBuilder_PTDE(NodeTreeBuilder):
    """Node tree builder for Demon's Souls. Basically the same as DeS but with more shaders and added detail bumpmap.
    """

    @property
    def _diffuse_map_color(self) -> tuple[float, ...]:
        """Get RGBA diffuse map color. Defaults to (1, 1, 1, 1)."""
        return tuple(float(x) for x in self.get_mtd_param("g_DiffuseMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _specular_map_color(self):
        return tuple(float(x) for x in self.get_mtd_param("g_SpecularMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _fresnel_color(self):
        return tuple(float(x) for x in self.get_mtd_param("g_FresnelColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    def build(self):
        self._initialize_node_tree()
        try:
            if self.matdef.shader_category == "Water":
                # Used by water surfaces.
                self._build_ds1_water_shader()
                return
            if self.matdef.shader_category == "NormalToAlpha":
                # Used by fog, lightshafts, and some tree leaves. Fades out the object when viewed side-on.
                self._build_ds1_normal_to_alpha_shader()
                return
            if "FRPG_Phn_ColDif" in self.matdef.shader_stem:
                if self.get_mtd_param("g_LightingType", default=1) == 0:
                    # If `g_LightingType == 0`, nothing matters but the final surface image.
                    # This shader is probably fine for all games, but should be verified.
                    self._build_ptde_diffuse_no_light_shader()
                    return
                else:
                    # Dir3 or Env surface shader
                    self._build_ptde_standard_shader()
                    return
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building Prepare to Die Edition special shader for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )
            return
        # Fall back to base node tree builder.
        super(NodeTreeBuilder_PTDE, self).build()

    def _build_ptde_standard_shader(self):
        # Tri-directional phong lighting, or cubemap environmental lighting shader (Dir3 or Env)
        self._build_primary_shader(node_group_name=
                                   "DS1 Standard Env Shader"
                                   if self.get_mtd_param("g_LightingType", default=1) == 3
                                   else "DS1 Standard Dir3 Shader",
                                   node_inputs=
                                   {
                                       "Diffuse Map": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Albedo",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                       ),
                                       "Diffuse Map Alpha": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Albedo",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                           alpha=True
                                       ) if self.matdef.edge or self.matdef.alpha else None,
                                       "Specular Map": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Specular",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                       ),
                                       "Normal": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Normal",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                           normal=True
                                       ) if
                                       self.get_mtd_param("g_DetailBump_BumpPower", default=0) <= 0
                                       else
                                       self._get_combined_normal_and_detail_socket(
                                           self._get_single_or_mixed_samplers(
                                               r"Main \d+ Normal",
                                               self.vertex_colors_nodes[0].outputs["Alpha"],
                                               normal=True
                                           )
                                       ),
                                       "Light Map": self._get_single_or_mixed_samplers(
                                           r"Lightmap",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                       ),
                                       "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                                       "Vertex Colors Alpha": None if self.matdef.has_name_tag("Multi")
                                                                      or not (
                                                   self.matdef.edge or self.matdef.alpha) else
                                       self.vertex_colors_nodes[0].outputs["Alpha"]
                                   },
                                   mtd_param_values=
                                   {
                                       "Diffuse Map Color": self._diffuse_map_color,
                                       "Diffuse Map Color Power": self.get_mtd_param(
                                           "g_DiffuseMapColorPower", default=1),
                                       "Specular Map Color": self._specular_map_color,
                                       "Specular Map Color Power": self.get_mtd_param(
                                           "g_SpecularMapColorPower", default=1),
                                       "Specular Power": self.get_mtd_param(
                                           "g_SpecularPower", default=2),
                                       "Light Map Influence":
                                           1 if self.tex_image_nodes.get("Lightmap", None)
                                           else 0
                                   },
                                   )

    def _build_ptde_diffuse_no_light_shader(self):
        """This shader is used for objects that don't receive lighting, like the skybox.
        """
        self._build_primary_shader(node_group_name="Generic Diffuse No Light",
                                   node_inputs=
                                   {
                                       "Diffuse Map": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Albedo",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                       ),
                                       "Diffuse Map Alpha": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Albedo",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                           alpha=True
                                       ) if self.matdef.edge or self.matdef.alpha else None,
                                       "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                                       "Vertex Colors Alpha": None if self.matdef.has_name_tag("Multi")
                                                                      or not (
                                               self.matdef.edge or self.matdef.alpha) else
                                       self.vertex_colors_nodes[0].outputs["Alpha"]
                                   },
                                   mtd_param_values=
                                   {
                                       "Diffuse Map Color": self._diffuse_map_color,
                                       "Diffuse Map Color Power":
                                           self.get_mtd_param("g_DiffuseMapColorPower", default=1),
                                   }
                                   )

    def _build_ds1_water_shader(self) -> bpy.types.ShaderNodeGroup:
        """Water shader. Uses the texture in the normal map sampler as a heightmap, sampled at 3 different tile scales.
        """
        tile_image = self.tex_image_nodes.get("Main 0 Normal").image
        uv_node = self.uv_nodes["UVTexture0"]
        water_color = self.get_mtd_param("g_WaterColor", default=(1, 1, 1, 1))
        shader_inputs = {
            "WaterFadeBegin":self.get_mtd_param("g_WaterFadeBegin", default=1),
            "FresnelColor": self._fresnel_color,
            "FresnelPower": self.get_mtd_param("g_FresnelPower", default=1),
            "FresnelBias": self.get_mtd_param("g_FresnelBias", default=0.5),
            "FresnelScale": self.get_mtd_param("g_FresnelScale", default=1),
            "WaterColor": water_color,
            "WaterColorAlpha":water_color[3],
            "RefractBand": self.get_mtd_param("g_RefractBand", default=1),
            "ReflectBand": self.get_mtd_param("g_ReflectBand", default=1),
            "WaterWaveHeight": self.get_mtd_param("g_WaterWaveHeight", default=1)
        }
        for i in range(0,3):
            heightmap_node = self._new_tex_image_node("Water Tile " + str(i), tile_image)
            uv_scale_node = self._new_tex_scale_node(
                Vector2(
                [self.get_mtd_param("g_TileScale_" + str(i), default=1),
                  self.get_mtd_param("g_TileScale_" + str(i), default=1)]
            )
            , heightmap_node.location.y
            )
            self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
            self.link(uv_scale_node.outputs["Vector"], heightmap_node.inputs[0])
            shader_inputs["TileHeight_" + str(i)] = heightmap_node.outputs["Color"]
            shader_inputs["TileBlend_" + str(i)] = self.get_mtd_param("g_TileBlend_" + str(i), default=0.1)

        if len(self.vertex_colors_nodes) > 0:
            shader_inputs["Vertex Colors Alpha"] = self.vertex_colors_nodes[0].outputs["Alpha"]

        return self._new_bsdf_shader_node_group(
            "DS1 Water",
            inputs=shader_inputs,
            outputs={0: self.output_surface},
        )

    def _build_ds1_normal_to_alpha_shader(self):
        """Same as the diffuse no-light shader, but also fades out the object past certain viewing angles."""
        self._build_primary_shader(node_group_name="DS1R Normal to Alpha",
                                   node_inputs=
                                   {
                                       "Diffuse Map": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Albedo",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                       ),
                                       "Diffuse Map Alpha": self._get_single_or_mixed_samplers(
                                           r"Main \d+ Albedo",
                                           self.vertex_colors_nodes[0].outputs["Alpha"],
                                           alpha=True
                                       ),
                                       "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                                       "Vertex Colors Alpha": self.vertex_colors_nodes[0].outputs["Alpha"]
                                   },
                                   mtd_param_values=
                                   {
                                       "Diffuse Map Color": self._diffuse_map_color,
                                       "Diffuse Map Color Power":
                                           self.get_mtd_param("g_DiffuseMapColorPower", default=1),
                                       "Min Angle": self.get_mtd_param("g_Normal2Alpha_MinAngle", default=90),
                                       "Max Angle": self.get_mtd_param("g_Normal2Alpha_MaxAngle", default=80)
                                   }
                                   )

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

    def _get_combined_normal_and_detail_socket(self, normal_socket: NodeSocket):
        detail_output_socket = self._get_detail_output_socket()
        if not detail_output_socket:
            return normal_socket

        combine_detail_node = self._new_normal_combine_node(
            node_y=normal_socket.node.location[1] - 150,
            inputs={0: normal_socket, 1: detail_output_socket},
            outputs=None,  # will replace the normal map input above
        )
        combine_detail_node.hide = True
        return combine_detail_node.outputs[0]