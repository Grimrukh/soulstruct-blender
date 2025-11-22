from __future__ import annotations

__all__ = [
    "NodeTreeBuilder_DeS",
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
class NodeTreeBuilder_DeS(NodeTreeBuilder):
    """Node tree builder for Demon's Souls.
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
            if "DS_Phn_ColDif" in self.matdef.shader_stem:
                if self.get_mtd_param("g_LightingType", default=1) == 0:
                    # If `g_LightingType == 0`, nothing matters but the final surface image.
                    # This shader is probably fine for all games, but should be verified.
                    self._build_des_diffuse_no_light_shader()
                    return
                else:
                    # Dir3 or Env surface shader
                    self._build_des_standard_shader()
                    return
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building Demon's Souls special shader for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )
            return
        # Fall back to base node tree builder.
        super(NodeTreeBuilder_DeS, self).build()

    def _build_des_standard_shader(self):
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

    def _build_des_diffuse_no_light_shader(self):
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

