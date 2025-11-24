from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

from dataclasses import dataclass

from bpy.types import NodeSocket, ShaderNodeGroup

from soulstruct.utilities.maths import Vector2

from soulstruct.blender.exceptions import MaterialImportError
from soulstruct.blender.flver.material.shaders.base_node_tree_builder import BaseNodeTreeBuilder, NODE_INPUT_VALUE_TYPING


@dataclass(slots=True)
class NodeTreeBuilder(BaseNodeTreeBuilder):
    """Node tree builder for Dark Souls 1: Prepare to Die Edition (2012).

    Basically the same as DeS but with more shaders and added detail bumpmap.
    """

    @property
    def _diffuse_map_color(self) -> tuple[float, ...]:
        """Get RGBA diffuse map color. Defaults to (1, 1, 1, 1)."""
        return tuple(float(x) for x in self.get_mtd_param("g_DiffuseMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _specular_map_color(self) -> tuple[float, ...]:
        return tuple(float(x) for x in self.get_mtd_param("g_SpecularMapColor", default=(1.0, 1.0, 1.0))) + (1.0,)

    @property
    def _fresnel_color(self) -> tuple[float, ...]:
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
                    self._build_ds1_diffuse_no_light_shader()
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
        super(NodeTreeBuilder, self).build()

    def _build_ptde_standard_shader(self):
        """Tri-directional phong lighting, or cubemap environmental lighting shader (Dir3 or Env)."""
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]

        if self.get_mtd_param("g_LightingType", default=1) == 3:
            node_group_name = "PTDE Standard Env Shader"
        else:
            node_group_name = "PTDE Standard Dir3 Shader"

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
                # PTDE ONLY (not DS1R):
                "Specular Power": self.get_mtd_param("g_SpecularPower", default=2),
                "Light Map Influence": 1 if self.tex_image_nodes.get("Lightmap", None) else 0,
            },
        )

    def _build_ds1_diffuse_no_light_shader(self):
        """This shader is used for objects that don't receive lighting, like the skybox."""
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        self._build_primary_shader(
            node_group_name="Generic Diffuse No Light",
            node_inputs={
                "Diffuse Map": self._get_mixed_texture_color(r"Main \d+ Albedo", vc_alpha),
                "Diffuse Map Alpha": self._get_mixed_texture_alpha(
                    r"Main \d+ Albedo", vc_alpha, self.matdef.edge or self.matdef.alpha
                ),
                "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_colors_alpha else None,
            },
            input_default_values={
                "Diffuse Map Color": self._diffuse_map_color,
                "Diffuse Map Color Power": self.get_mtd_param("g_DiffuseMapColorPower", default=1),
            },
        )

    def _build_ds1_water_shader(self) -> ShaderNodeGroup:
        """Water shader for PTDE and DS1R.

        Uses the texture in the normal map sampler as a heightmap, sampled at 3 different tile scales.
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
        }  # type: dict[str, NODE_INPUT_VALUE_TYPING | NodeSocket]

        for i in range(0,3):
            heightmap_node = self._new_tex_image_node(f"Water Tile {i}", tile_image)
            uv_scale_node = self._new_tex_scale_node(
                Vector2([
                    self.get_mtd_param(f"g_TileScale_{i}", default=1),
                    self.get_mtd_param(f"g_TileScale_{i}", default=1),
                ]),
                node_y=heightmap_node.location.y,
            )
            self.link(uv_node.outputs["Vector"], uv_scale_node.inputs[0])
            self.link(uv_scale_node.outputs["Vector"], heightmap_node.inputs[0])
            shader_inputs[f"TileHeight_{i}"] = heightmap_node.outputs["Color"]
            shader_inputs[f"TileBlend_{i}"] = self.get_mtd_param(f"g_TileBlend_{i}", default=0.1)

        if len(self.vertex_colors_nodes) > 0:
            shader_inputs["Vertex Colors Alpha"] = self.vertex_colors_nodes[0].outputs["Alpha"]

        return self._new_bsdf_shader_node_group(
            "DS1 Water",
            inputs=shader_inputs,
            outputs={0: self.output_surface},
        )

    def _build_ds1_normal_to_alpha_shader(self):
        """Same as the diffuse no-light shader, but also fades out the object past certain viewing angles."""
        vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        self._build_primary_shader(
            node_group_name="DS1 Normal to Alpha",
            node_inputs={
                "Diffuse Map": self._get_mixed_texture_color(r"Main \d+ Albedo", vc_alpha),
                "Diffuse Map Alpha": self._get_mixed_texture_alpha(r"Main \d+ Albedo", vc_alpha),
                "Vertex Colors": self.vertex_colors_nodes[0].outputs["Color"],
                "Vertex Colors Alpha": vc_alpha,
            },
            input_default_values={
                "Diffuse Map Color": self._diffuse_map_color,
                "Diffuse Map Color Power": self.get_mtd_param("g_DiffuseMapColorPower", default=1),
                "Min Angle": self.get_mtd_param("g_Normal2Alpha_MinAngle", default=90),
                "Max Angle": self.get_mtd_param("g_Normal2Alpha_MaxAngle", default=80),
            },
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

    @property
    def _uses_vertex_colors_alpha(self) -> bool:
        return not (self.matdef.has_name_tag("Multi") or not (self.matdef.edge or self.matdef.alpha))
