from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

from dataclasses import dataclass

from soulstruct.utilities.maths import Vector2

from .....exceptions import MaterialImportError
from ..darksouls1ptde.node_tree_builder import NodeTreeBuilder as PTDENodeTreeBuilder
from ..enums import SoulstructNodeGroups


@dataclass(slots=True)
class NodeTreeBuilder(PTDENodeTreeBuilder):
    """Node tree builder for Dark Souls: Remastered (2018).

    Extends the PTDE node tree builder with new/modified DS1R-specific shaders.
    
    Thanks to @thegreatgramcracker for implementing the pre-baked node groups and build logic for DS1R.
    """

    USES_RG_NORMALS = True

    def build(self):
        self._initialize_node_tree()
        try:
            if "Water" in self.matdef.shader_stem:
                # Used by water surfaces.
                self._build_ds1_water_shader()
                return
            if "Snow" in self.matdef.shader_stem:
                # Used by snow surfaces (DS1R only).
                self._build_ds1r_snow_shader()
                return
            if "NormalToAlpha" in self.matdef.shader_stem:
                # Used by fog, lightshafts, and some tree leaves. Fades out the object when viewed side-on.
                self._build_ds1_normal_to_alpha_shader()
                return
            if "FRPG_Phn_ColDif" in self.matdef.shader_stem or "FRPG_Sfx_ColDif" in self.matdef.shader_stem:
                if self.get_param("g_LightingType", default=1) == 0:
                    # If `g_LightingType == 0`, nothing matters but the final surface image.
                    # This shader is probably fine for all games, but should be verified.
                    self._build_ds1_diffuse_no_light_shader()
                    return
                else:
                    # PBR or Legacy (colored specular) surface shader.
                    self._build_ds1r_standard_shader()
                    return
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building Dark Souls: Remastered special shader for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )
            return

        self.operator.warning(
            f"No DS1R shader support for MatDef {self.matdef.name} with shader {self.matdef.shader_stem}."
        )

    def _build_ds1r_standard_shader(self):
        """PBR or Legacy (colored specular) workflow."""
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        if self.get_param("g_MaterialWorkflow", default=0) == 0:
            node_group = SoulstructNodeGroups.DS1RBasicPBRShader
        else:
            node_group = SoulstructNodeGroups.DS1RBasicColoredSpecShader

        normal_socket, _ = self._get_mixed_texture_normals(r"DSB \d+ Normal", vc_alpha)
        if normal_socket and self.get_param("g_DetailBump_BumpPower", default=0) > 0:
            normal_socket = self._get_combined_normal_and_detail_socket(normal_socket)

        self._new_bsdf_shader_node_group(
            node_group,
            inputs={
                "Diffuse Map": self._get_mixed_texture_color(r"DSB \d+ Diffuse", vc_alpha),
                "Diffuse Map Color": self._diffuse_map_color,
                "Diffuse Map Color Power": self.get_param("g_DiffuseMapColorPower", default=1),
                "Diffuse Map Alpha": self._get_mixed_texture_alpha(
                    r"DSB \d+ Diffuse", vc_alpha, self.matdef.edge or self.matdef.alpha,
                ),
                "Specular Map": self._get_mixed_texture_color(r"DSB \d+ Specular", vc_alpha),
                "Specular Map Color": self._specular_map_color,
                "Specular Map Color Power": self.get_param("g_SpecularMapColorPower", default=1),
                # Specular Power removed since PTDE.
                # NEW in DS1R (not PTDE):
                "Specular Map Alpha": self._get_mixed_texture_alpha(r"DSB \d+ Specular", vc_alpha),
                "Normal": normal_socket,
                "Light Map": self._get_mixed_texture_color(r"Lightmap", vc_alpha),
                "Light Map Influence": 1 if self.tex_image_nodes.get("Lightmap", None) else 0,
                "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_colors_alpha else None,
            },
            outputs={
                "Shader": self.output_surface,
            }
        )

    def _build_ds1r_snow_shader(self):
        """Builds the DS1R Snow shader.

        This is the most complex shader by far in terms of weird inputs. The subsurface scattering and parallax
        occlusion are not accurately depicted (maybe in Blender 5 when parallax is a built-in node).

        TODO: Use Blender 5 parallax node.
        """
        height_image = self.tex_image_nodes.get("Snow Height").image
        uv_node = self.uv_nodes["UVTexture0"]
        inputs = {
            "Diffuse Map" : self._get_mixed_texture_color("DSB 0 Diffuse"),
            "Diffuse Map Color": self._diffuse_map_color,
            "Diffuse Map Color Power": self.get_param("g_DiffuseMapColorPower", default=1),

            "Specular Map": self._get_mixed_texture_color("DSB 0 Specular"),
            "Specular Map Color": self._specular_map_color,
            "Specular Map Color Power": self.get_param("g_SpecularMapColorPower", default=1),

            "Normal": self._get_mixed_texture_normals(r"DSB 0 Normal")[0],

            "Snow Color" : self.get_param("g_SnowColor", default=(1, 1, 1, 1)),
            "Snow Height" : self.get_param("g_SnowHeight", default=0.6),
            "Snow Detail": self._get_mixed_texture_normals("Snow Detail Normal")[0],
            "Diffuse Top Height": self.get_param("g_SnowDiffuseBlendTopHeight", default=0.15),
            "Diffuse Bottom Height": self.get_param("g_SnowDiffuseBlendBottomHeight", default=0.1),
            "Snow Delta Height Limit": self.get_param("g_SnowDeltaHeightLimit", default=0.02),

            "Light Map" : self._get_mixed_texture_color(r"Lightmap"),
        }
        for i in range(3):
            # Three different repeats of the snow tile at different scales.
            heightmap_node = self._new_tex_image_node(
                f"[No Export] Snow Tile {i}", height_image, label=f"Snow Tile {i}"
            )
            uv_scale_node = self._new_tex_scale_node(
                Vector2([
                    self.get_param(f"g_SnowTileScale_{i}", default=1),
                    self.get_param(f"g_SnowTileScale_{i}", default=1),
                ]),
                node_y=heightmap_node.location.y,
            )
            self.link(uv_node.outputs["UV"], uv_scale_node.inputs[0])
            self.link(uv_scale_node.outputs["Vector"], heightmap_node.inputs[0])
            inputs[f"Snow Tile Height {i}"] = heightmap_node.outputs["Color"]
            inputs[f"Snow Tile Blend {i}"] = self.get_param(f"g_SnowTileBlend_{i}", default=0.1)

        if "Lightmap" in self.tex_image_nodes:
            self.link(self.uv_nodes["UVLightmap"].outputs["Vector"], self.tex_image_nodes["Lightmap"].inputs["Vector"])
            inputs["Light Map Influence"] = 1.0

        if inputs["Snow Detail"]:
            snow_detail_samp = self.tex_image_nodes["DSB 1 Normal"]
            uv_scale_node = self._new_tex_scale_node(
                Vector2([
                    self.get_param("g_SnowDetailBumpTileScale", default=1),
                    self.get_param("g_SnowDetailBumpTileScale", default=1),
                ]),
                node_y=snow_detail_samp.location.y,
            )
            # Despite the mtd saying the detail bumpmap in g_Bumpmap_2 is UV #2 (UVTexture1), for some reason it
            # actually uses UVTexture0 based on testing.
            self.link(uv_node.outputs["UV"], uv_scale_node.inputs[0])
            self.link(uv_scale_node.outputs["Vector"], snow_detail_samp.inputs[0])
            # Also means we have to set the normal map UV Map to UVTexture0.
            normal_node = inputs["Snow Detail"].node
            normal_node.inputs["Strength"].default_value = self.get_param("g_SnowDetailBumpPower", default=0)
            normal_node.uv_map = "UVTexture0"

        if len(self.vertex_colors_nodes) > 0:
            inputs["Vertex Colors Alpha"] = self.vertex_colors_nodes[0].outputs["Alpha"]

        self._new_bsdf_shader_node_group(
            SoulstructNodeGroups.DS1RSnowShader,
            inputs=inputs,
            outputs={"Shader": self.output_surface},
        )
