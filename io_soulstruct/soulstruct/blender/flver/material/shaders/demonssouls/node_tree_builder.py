from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

from dataclasses import dataclass

from .....exceptions import MaterialImportError
from ..base_node_tree_builder import BaseNodeTreeBuilder
from ..enums import SoulstructNodeGroups


@dataclass(slots=True)
class NodeTreeBuilder(BaseNodeTreeBuilder):
    """Node tree builder for Demon's Souls (2009)."""

    @property
    def _diffuse_map_color(self) -> tuple[float, ...]:
        """Get RGBA diffuse map color. Defaults to (1, 1, 1, 1)."""
        return self.get_param("g_DiffuseMapColor", default=(1.0, 1.0, 1.0)) + (1.0,)

    @property
    def _specular_map_color(self) -> tuple[float, ...]:
        return self.get_param("g_SpecularMapColor", default=(1.0, 1.0, 1.0)) + (1.0,)

    @property
    def _fresnel_color(self) -> tuple[float, ...]:
        return self.get_param("g_FresnelColor", default=(1.0, 1.0, 1.0)) + (1.0,)

    def build(self):
        self._initialize_node_tree()
        try:
            if "DS_Phn_ColDif" in self.matdef.shader_stem:
                if self.get_param("g_LightingType", default=1) == 0:
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

        self.operator.warning(
            f"No DeS shader support for MatDef {self.matdef.name} with shader {self.matdef.shader_stem}."
        )

    def _build_des_standard_shader(self):
        """Tri-directional Phong lighting, or cubemap environmental lighting shader (Dir3 or Env)."""
        node_group = (
            SoulstructNodeGroups.PTDEStandardEnvShader
            if self.get_param("g_LightingType", default=1) == 3
            else SoulstructNodeGroups.PTDEStandardDir3Shader
        )
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]

        self._new_bsdf_shader_node_group(
            node_group,
            inputs={
                "Diffuse Map": self._get_mixed_texture_color(r"DSB \d+ Diffuse", vc_alpha),
                "Diffuse Map Color": self._diffuse_map_color,
                "Diffuse Map Color Power": self.get_param("g_DiffuseMapColorPower", default=1),
                "Diffuse Map Alpha": self._get_mixed_texture_alpha(
                    r"DSB \d+ Diffuse", vc_alpha
                ) if self.matdef.edge or self.matdef.alpha else None,

                "Specular Map": self._get_mixed_texture_color(r"DSB \d+ Specular", vc_alpha),
                "Specular Map Color": self._specular_map_color,
                "Specular Map Color Power": self.get_param("g_SpecularMapColorPower", default=1),
                "Specular Power": self.get_param("g_SpecularPower", default=2),

                "Normal": self._get_mixed_texture_normals(r"DSB \d+ Normal", vc_alpha)[0],

                "Light Map": self._get_mixed_texture_color(r"Lightmap", vc_alpha),
                "Light Map Influence": 1 if self.tex_image_nodes.get("Lightmap", None) else 0,

                "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_color_alpha else None,
            },
            outputs={"Shader": self.output_surface},
        )

    def _build_des_diffuse_no_light_shader(self):
        """This shader is used for objects that don't receive lighting, like the skybox."""
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        self._new_bsdf_shader_node_group(
            SoulstructNodeGroups.GenericDiffuseNoLightShader,
            inputs={
                "Diffuse Map": self._get_mixed_texture_color(r"DSB \d+ Diffuse", vc_alpha),
                "Diffuse Map Color": self._diffuse_map_color,
                "Diffuse Map Color Power": self.get_param("g_DiffuseMapColorPower", default=1),
                "Diffuse Map Alpha": self._get_mixed_texture_alpha(
                    r"DSB \d+ Diffuse", vc_alpha
                ) if self.matdef.edge or self.matdef.alpha else None,
                "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_color_alpha else None,
            },
            outputs={"Shader": self.output_surface},
       )

    @property
    def _uses_vertex_color_alpha(self) -> bool:
        return not (self.matdef.has_name_tag("Multi") or (not self.matdef.edge and not self.matdef.alpha))
