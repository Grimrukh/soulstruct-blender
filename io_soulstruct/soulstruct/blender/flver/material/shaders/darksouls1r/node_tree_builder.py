from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

from dataclasses import dataclass

from soulstruct.utilities.maths import Vector2

from soulstruct.blender.exceptions import MaterialImportError
from soulstruct.blender.flver.material.shaders.darksouls1ptde.ptde_node_tree_builder import NodeTreeBuilder as PTDENodeTreeBuilder


@dataclass(slots=True)
class NodeTreeBuilder(PTDENodeTreeBuilder):
    """Node tree builder for Dark Souls: Remastered (2018).

    Extends the PTDE node tree builder with new/modified DS1R-specific shaders.
    
    Thanks to @thegreatgramcracker for implementing the pre-baked node groups and build logic for DS1R.
    """

    def build(self):
        self._initialize_node_tree()
        try:
            if self.matdef.shader_category == "Water":
                # Used by water surfaces.
                self._build_ds1_water_shader()
                return
            if self.matdef.shader_category == "Snow":
                # Used by snow surfaces (DS1R only).
                self._build_ds1r_snow_shader()
                return
            if self.matdef.shader_category == "NormalToAlpha":
                # Used by fog, lightshafts, and some tree leaves. Fades out the object when viewed side-on.
                self._build_ds1_normal_to_alpha_shader()
                return
            if "FRPG_Phn_ColDif" in self.matdef.shader_stem or "FRPG_Sfx_ColDif" in self.matdef.shader_stem:
                if self.get_mtd_param("g_LightingType", default=1) == 0:
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

        # Fall back to base node tree builder.
        super(NodeTreeBuilder, self).build()

    def _build_ds1r_standard_shader(self):
        """PBR or Legacy (colored specular) workflow."""
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        if self.get_mtd_param("g_MaterialWorkflow", default=0) == 0:
            node_group_name = "DS1R Basic PBR"
        else:
            node_group_name = "DS1R Basic Colored Spec"

        normal_socket = self._get_mixed_texture_normals(r"Main \d+ Normal", vc_alpha)
        if self.get_mtd_param("g_DetailBump_BumpPower", default=0) > 0:
            normal_socket = self._get_combined_normal_and_detail_socket(normal_socket)

        self._build_primary_shader(
            node_group_name=node_group_name,
            node_inputs={
                "Diffuse Map": self._get_mixed_texture_color(r"Main \d+ Albedo", vc_alpha),
                "Diffuse Map Alpha": self._get_mixed_texture_alpha(
                    r"Main \d+ Albedo", vc_alpha, self.matdef.edge or self.matdef.alpha,
                ),
                "Specular Map": self._get_mixed_texture_color(r"Main \d+ Specular", vc_alpha),
                # NEW in DS1R (not PTDE):
                "Specular Map Alpha": self._get_mixed_texture_alpha(r"Main \d+ Specular", vc_alpha),
                "Normal": normal_socket,
                "Light Map": self._get_mixed_texture_color(r"Lightmap", vc_alpha),
                "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_colors_alpha else None,
            },
            input_default_values={
                "Diffuse Map Color": self._diffuse_map_color,
                "Diffuse Map Color Power": self.get_mtd_param("g_DiffuseMapColorPower", default=1),
                "Specular Map Color": self._specular_map_color,
                "Specular Map Color Power": self.get_mtd_param("g_SpecularMapColorPower", default=1),
                # Specular Power removed since PTDE.
                "Light Map Influence": 1 if self.tex_image_nodes.get("Lightmap", None) else 0,
            },
        )

    def _build_ds1r_snow_shader(self):
        """Builds the DS1R Snow shader.

        This is the most complex shader by far in terms of weird inputs. The subsurface scattering and parallax
        occlusion are not accurately depicted (maybe in Blender 5 when parallax is a built-in node).
        """
        height_image = self.tex_image_nodes.get("Main 0 Normal").image
        uv_node = self.uv_nodes["UVTexture0"]
        node_inputs = {
            "Diffuse Map" : self._get_mixed_texture_color(r"Main 0 Albedo"),
            "Specular Map": self._get_mixed_texture_color(r"Main 0 Specular"),
            "Normal": self._get_mixed_texture_normals(r"Main 2 Normal"),
            "Snow Detail": self._get_mixed_texture_normals(r"Main 1 Normal"),
            "Light Map" : self._get_mixed_texture_color(r"Lightmap"),
        }
        input_default_values = {
            "Diffuse Map Color" : self._diffuse_map_color,
            "Diffuse Map Color Power" : self.get_mtd_param("g_DiffuseMapColorPower", default=1),
            "Specular Map Color": self._specular_map_color,
            "Specular Map Color Power": self.get_mtd_param("g_SpecularMapColorPower", default=1),
            "Snow Color" : self.get_mtd_param("g_SnowColor", default=(1, 1, 1, 1)),
            "Snow Height" : self.get_mtd_param("g_SnowHeight", default=0.6),
            "Diffuse Top Height": self.get_mtd_param("g_SnowDiffuseBlendTopHeight", default=0.15),
            "Diffuse Bottom Height": self.get_mtd_param("g_SnowDiffuseBlendBottomHeight", default=0.1),
            "Snow Delta Height Limit": self.get_mtd_param("g_SnowDeltaHeightLimit", default=0.02),
        }
        for i in range(0,3):
            heightmap_node = self._new_tex_image_node(f"Snow Tile {i}", height_image)
            uv_scale_node = self._new_tex_scale_node(
                Vector2([
                    self.get_mtd_param(f"g_SnowTileScale_{i}", default=1),
                    self.get_mtd_param(f"g_SnowTileScale_{i}", default=1),
                ]),
                node_y=heightmap_node.location.y,
            )
            self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
            self.link(uv_scale_node.outputs["Vector"], heightmap_node.inputs[0])
            node_inputs[f"Snow Tile Height {i}"] = heightmap_node.outputs["Color"]
            input_default_values[f"Snow Tile Blend {i}"] = self.get_mtd_param(f"g_SnowTileBlend_{i}", default=0.1)

        if "Lightmap" in self.tex_image_nodes:
            #Reroute UVTexture1 to lightmap node. It's weird, but uv lightmap is NOT being used based on testing.
            self.link(self.uv_nodes["UVTexture1"].outputs["Vector"], self.tex_image_nodes["Lightmap"].inputs["Vector"])
            input_default_values["Light Map Influence"] = 1.0

        if node_inputs["Snow Detail"]:
            snow_detail_samp = self.tex_image_nodes["Main 1 Normal"]
            uv_scale_node = self._new_tex_scale_node(
                Vector2([
                    self.get_mtd_param("g_SnowDetailBumpTileScale", default=1),
                    self.get_mtd_param("g_SnowDetailBumpTileScale", default=1),
                ]),
                node_y=snow_detail_samp.location.y,
            )
            # Despite the mtd saying the detail bumpmap in g_Bumpmap_2 is UV #2 (UVTexture1), for some reason it
            # actually uses UVTexture0 based on testing.
            self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
            self.link(uv_scale_node.outputs["Vector"], snow_detail_samp.inputs[0])
            # Also means we have to set the normal map UV Map to UVTexture0.
            normal_node = node_inputs["Snow Detail"].node
            normal_node.inputs["Strength"].default_value = self.get_mtd_param("g_SnowDetailBumpPower", default=0)
            normal_node.uv_map = "UVTexture0"

        if len(self.vertex_colors_nodes) > 0:
            node_inputs["Vertex Colors Alpha"] = self.vertex_colors_nodes[0].outputs["Alpha"]
        self._build_primary_shader(
            "DS1R Snow Shader", node_inputs=node_inputs, input_default_values=input_default_values
        )
