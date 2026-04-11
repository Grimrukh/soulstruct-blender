from __future__ import annotations

__all__ = [
    "NodeTreeBuilder",
]

from dataclasses import dataclass

from soulstruct.eldenring.models.shaders import MatDef
from ..utilities import new_soulstruct_node_group

from .....exceptions import MaterialImportError
from ..base_node_tree_builder import BaseNodeTreeBuilder
from ..enums import SoulstructNodeGroups


@dataclass(slots=True)
class NodeTreeBuilder(BaseNodeTreeBuilder):
    """Node tree builder for Elden Ring (2022)."""

    # Type override: Elden Ring MatDef.
    matdef: MatDef

    ALBEDO_COLOR_SPACE = "Non-Color"
    USES_RG_NORMALS = True

    @property
    def _diffuse_map_color(self) -> tuple[float, ...]:
        """Get RGBA diffuse map color. Defaults to (1, 1, 1, 1).

        TODO: MATBIN field exists and does vary, but not confirmed.
        """
        color = self.get_param("g_DiffuseMapColor", default=(1.0, 1.0, 1.0)) + (1.0,)
        return tuple(float(x) for x in color)

    @property
    def _metallic_map_color(self) -> tuple[float, ...]:
        # TODO: Not sure where to find this in ER.
        return 1.0, 1.0, 1.0, 1.0

    def build(self):
        self.operator.info(f"Building Elden Ring node tree for material definition {self.matdef.name}.")

        self._initialize_node_tree()

        # TODO: Add special Elden Ring shaders.

        if "[Eye]" in self.matdef.shader_stem:
            print("EYE PARAMS:")
            for k, v in self.matdef.matbin_params.items():
                print(f"  {k} = {v}")
        if "[DetailBlend][S2]" in self.matdef.shader_stem:
            print("DetailBlend S2 params:")
            for k, v in self.matdef.matbin_params.items():
                print(f"  {k} = {v}")

        try:
            if "[Fur]" in self.matdef.shader_stem:
                self._build_er_fur_shader()
                return

            if "ThreeNormals 0 Normal_0" in self.tex_image_nodes:
                self._build_er_threenormals_shader()
                return

            # Generic builder for all other unhandled material categories.
            self._build_er_standard_shader()
            return
        except MaterialImportError as ex:
            self.operator.warning(
                f"Error building shader for material '{self.matdef.name}' with shader '{self.matdef.shader_stem}'. "
                f"Error:\n    {ex}"
            )

        # TODO: Not currently reachable.
        self.operator.warning(
            f"No ER shader support for MatDef {self.matdef.name} with shader {self.matdef.shader_stem}."
        )

    def _build_er_fur_shader(self):
        """Build a Blender shader for Elden Ring '[Fur]' shaders."""

        # TODO: Still need to blend details for [DetailBlend].

        normal_socket, shininess_socket = self._get_mixed_texture_normals("AlbedoNormal 0 Normal")

        self._new_bsdf_shader_node_group(
            SoulstructNodeGroups.ERFurShader,
            inputs={
                "Albedo Map": self._get_mixed_texture_color("AMN 0 Albedo"),
                "Albedo Map Color": self._diffuse_map_color,
                "Albedo Map Alpha": self._get_mixed_texture_alpha("AlbedoNormal 0 Albedo"),
                "Normal": normal_socket,
                "Shininess": shininess_socket,
                "Vertex Colors": None,
                "Vertex Colors Alpha": self.vertex_colors_nodes[0].outputs["Alpha"],
            },
            outputs={"Shader": self.output_surface},
        )

    def _build_er_threenormals_shader(self):
        """Build a Blender shader for Elden Ring shaders using three blended normals.

        TODO: Always used by [Face] shaders? Or [S2]?
        """

        try:
            vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        except IndexError:
            vc_alpha = 1.0

        mask3_map = self.tex_image_nodes["AlbedoNormalMask3 0 Mask3"]

        def _process_normals(sampler_alias: str):
            sampler = self.matdef.get_sampler_with_alias(sampler_alias)
            if not sampler:
                print(self.matdef.samplers)
                raise ValueError(f"{sampler_alias} sampler not found for Mask3 shader.")
            try:
                tex_image_node = self.tex_image_nodes[sampler_alias]
            except KeyError:
                raise ValueError(f"No image texture node present for {sampler_alias}.")

            return self._normal_tex_to_normal_input(
                y=tex_image_node.location[1],
                color_input_from=tex_image_node.outputs["Color"],
                normal_output_to=None,
                uv_layer_name=sampler.uv_layer_name,
            )

        main_normal_map_node, main_blue_passthru = _process_normals("AlbedoNormalMask3 0 Normal")

        inputs = {
            "Primary Normal": main_normal_map_node.outputs["Normal"],
            "Primary Shininess": main_blue_passthru,
            "Mask3 Map": mask3_map.outputs["Color"],
            "Mask3 Normalization": 0.2,  # TODO: source?
        }

        for i in range(3):
            normal_map_node_to_blend, blue_passthru_to_blend = _process_normals(f"ThreeNormals 0 Normal_{i}")
            assert blue_passthru_to_blend is not None
            inputs[f"Normal {i}"] = normal_map_node_to_blend.outputs["Normal"]
            inputs[f"Shininess {i}"] = blue_passthru_to_blend

        mask3_normals_blend = new_soulstruct_node_group(
            self.tree,
            SoulstructNodeGroups.ERMask3BlendNormals,
            location=(self.POST_TEX_X, mask3_map.location[1]),
            inputs=inputs,
        )

        self._new_bsdf_shader_node_group(
            SoulstructNodeGroups.ERBasicPBRShader,
            inputs={
                "Albedo Map": self._get_mixed_texture_color("AlbedoNormalMask3 0 Albedo"),
                "Albedo Map Color": self._diffuse_map_color,
                "Albedo Map Color Power": 1,  # TODO
                "Albedo Map Alpha": 1.0,  # TODO: assuming no skin alpha
                "Normal": mask3_normals_blend.outputs["Normal"],
                "Shininess": mask3_normals_blend.outputs["Shininess"],
                # TODO: ER uses the red VC channel for something - darkening, or ambient occlusion? e.g. Blaidd fur?
                "Vertex Colors": None,
                # TODO: ER definitely uses VC alpha for true transparency for some shaders.
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_colors_alpha else None,
            },
            outputs={"Shader": self.output_surface},
        )

        # TODO: Auto-setting UV scale to 20.0.
        tex_node = self.tex_image_nodes["ThreeNormals 0 Normal_0"]
        uv_scale_node = tex_node.inputs["Vector"].links[0].from_node
        if uv_scale_node:
            uv_scale_node.inputs[1].default_value = [20.0, 20.0, 1.0]

    def _build_er_standard_shader(self):
        """Standard Elden Ring AMSN-based workflow (e.g. 'C[DetailBlend]')."""
        try:
            vc_alpha = self.vertex_colors_nodes[0].outputs["Alpha"]
        except IndexError:
            vc_alpha = 1.0

        # TODO: Mixing Fac should come from Blend01 map, if present.
        # TODO: Don't mix 0.5 if one source is empty...
        mix_fac = 0.5

        # TODO: Just using 'main' normal for now.
        normal_socket, shininess_socket = self._get_mixed_texture_normals("AMN 0 Normal", mix_fac)

        self._new_bsdf_shader_node_group(
            SoulstructNodeGroups.ERBasicPBRShader,
            inputs={
                "Albedo Map": self._get_mixed_texture_color(r"AMN \d Albedo", mix_fac),
                "Albedo Map Color": self._diffuse_map_color,
                "Albedo Map Color Power": 1,  # TODO
                # TODO: Alpha comes strictly from AMN 0 Albedo, not mixed?
                "Albedo Map Alpha": self._get_mixed_texture_alpha(
                    "AMN 0 Albedo", 0.0
                ) if self.matdef.edge or self.matdef.alpha or self.matdef.cloth else None,
                "Metallic Map": self._get_mixed_texture_color(r".* \d Metallic", mix_fac),
                "Metallic Map Color": self._metallic_map_color,
                "Metallic Map Color Power": 1,  # TODO
                # TODO: I don't think ER ever uses the alpha channel of Metallic maps.
                "Metallic Map Alpha": None,
                "Normal": normal_socket,
                "Shininess": shininess_socket,
                "Shininess Map": self._get_mixed_texture_color(r".* \d Shininess", mix_fac),
                # TODO: Don't believe ER uses light map textures.
                # "Light Map": self._get_mixed_texture_color(r"Lightmap", vc_alpha),
                # "Light Map Influence": 1 if self.tex_image_nodes.get("Lightmap", None) else 0,
                # TODO: ER uses the red VC channel for something - darkening, or ambient occlusion? e.g. Blaidd fur?
                "Vertex Colors": None,
                # TODO: ER definitely uses VC alpha for true transparency for some shaders.
                "Vertex Colors Alpha": vc_alpha if self._uses_vertex_colors_alpha else None,
            },
            outputs={"Shader": self.output_surface},
        )

    @property
    def _uses_vertex_colors_alpha(self) -> bool:
        return not (self.matdef.has_name_tag("Multi") or not (self.matdef.edge or self.matdef.alpha))
