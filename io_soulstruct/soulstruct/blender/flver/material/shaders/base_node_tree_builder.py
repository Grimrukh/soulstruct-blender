from __future__ import annotations

__all__ = [
    "BaseNodeTreeBuilder",
]

import abc
import re
import typing as tp
from dataclasses import dataclass, field

import bpy
from bpy.types import NodeSocket

from soulstruct.base.models.shaders import MatDef
from soulstruct.eldenring.models.shaders import MatDef as ERMatDef
from soulstruct.utilities.maths import Vector2

from ....base.operators import LoggingOperator
from ....exceptions import MaterialImportError
from ...image.utilities import find_or_create_image
from .enums import SoulstructNodeGroups
from .utilities import *


@dataclass(slots=True)
class BaseNodeTreeBuilder(abc.ABC):
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials.

    Manages state intended for one single `context` and one `build()` call.

    This ABC must be implemented by each supported game.

    NOTES:
        # pow(2.0 / (max(fSpecPower * 4.0, 1.0) + 2.0), 0.25) for converting spec power to roughness from StaydMcMuffin
    """

    operator: LoggingOperator
    context: bpy.types.Context
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
    # Maps common, non-game-specific sampler type (e.g. 'Main 0 Albedo') to Nodes.
    tex_image_nodes: dict[str, bpy.types.Node] = field(default_factory=dict)

    tree: bpy.types.NodeTree = field(init=False)
    output: bpy.types.Node = field(init=False)

    # X coordinates of node type columns.
    VERTEX_COLORS_X: tp.ClassVar[float] = -950
    UV_X: tp.ClassVar[float] = -950
    SCALE_X: tp.ClassVar[float] = -750
    TEX_X: tp.ClassVar[float] = -550
    POST_TEX_X: tp.ClassVar[float] = -250  # overlay, split, math, normal map, etc.
    BSDF_X: tp.ClassVar[float] = -50
    MIX_X: tp.ClassVar[float] = 100

    # region Game-Specific Settings

    # Color space of Albedo (diffuse) textures.
    # All non-Albedo textures are 'Non-Color' in all games.
    ALBEDO_COLOR_SPACE: tp.ClassVar[str] = "sRGB"

    # Indicates if game uses RG normals that require blue to be computed.
    USES_RG_NORMALS: tp.ClassVar[bool] = False

    # endregion

    def __post_init__(self):
        if not self.material.node_tree:
            raise ValueError("Material has no shader node tree.")
        self.tree = self.material.node_tree
        self.output = self.tree.nodes["Material Output"]

    @abc.abstractmethod
    def build(self) -> None:
        """Build a shader node tree using shader/sampler information from given `MatDef`."""
        ...

    def build_shader_uv_texture_nodes(self):
        """Build UV and texture nodes. Used by all games."""

        self.uv_nodes = {}
        self.tex_image_nodes = {}  # type: dict[str, bpy.types.ShaderNodeTexImage]
        uv_scale_nodes = {}

        # We add Image Texture nodes in `MatDef` order, not FLVER order.
        # This is because in later games, MatDef samplers are already nicely grouped together from metaparam.

        current_sampler_group = self.matdef.samplers[0].sampler_group
        for sampler in self.matdef.samplers:

            # NOTE: We create UV texture nodes even for samplers with `is_uv_unused = True`, just so the material is
            # properly represented as it exists in the MTD/MATBIN. The FLVER exporter checks the MTD/MATBIN again and
            # does not care if these nodes are present.

            uv_layer_name = sampler.uv_layer_name
            # We assign the sampler alias to the node label, but preserve the game-specific sampler name in the node
            # name for inspection. The alias label is useful for porting this FLVER with its material to other games.
            node_name = sampler.name
            node_label = sampler.alias  # will be the same as `name` if alias could not be determined by `MatDef`

            if sampler.sampler_group != current_sampler_group:
                # Add extra Y offset to visually separate new group.
                self.tex_y -= 100
                current_sampler_group = sampler.sampler_group

            bl_image = self.get_sampler_bl_image(sampler.name)
            tex_image_node = self._new_tex_image_node(
                name=node_name, image=bl_image, label=node_label, hide=bl_image is None
            )

            # Dictionary keys are sampler aliases, not game-specific sampler names (though alias may fall back to that).
            self.tex_image_nodes[node_label] = tex_image_node

            # We take this opportunity to change the Color Space of non-Albedo textures to 'Non-Color'.
            # NOTE: If the texture is used inconsistently across materials, this could change repeatedly.
            if bl_image:
                if "Albedo" not in node_label and "Lightmap" not in node_label:
                    # noinspection PyTypeChecker
                    bl_image.colorspace_settings.name = "Non-Color"  # always
                else:
                    # noinspection PyTypeChecker
                    bl_image.colorspace_settings.name = self.ALBEDO_COLOR_SPACE  # game-dependent
            if uv_layer_name:
                # Connect to appropriate UV node, creating it if necessary.
                if uv_layer_name in self.uv_nodes:
                    uv_node = self.uv_nodes[uv_layer_name]
                else:
                    uv_node = self.uv_nodes[uv_layer_name] = self._new_uv_map_node(uv_layer_name)
                if sampler.uv_scale is not None:
                    # Elden Ring materials define extra scaling for certain sampler groups. We replicate it to produce
                    # a more faithful shader in Blender. None of this is exported to FLVER.
                    if sampler.sampler_group >= 1:
                        # Non-zero groups share UV scale, and so they share one node here.
                        if sampler.sampler_group in uv_scale_nodes:
                            uv_scale_node = uv_scale_nodes[sampler.sampler_group]
                        else:
                            # First occurrence of group. Create UV scale node.
                            uv_scale_node = self._new_tex_scale_node(sampler.uv_scale, tex_image_node.location.y)
                            uv_scale_nodes[sampler.sampler_group] = uv_scale_node
                    else:
                        # Group 0 should never have UV scale defined in MATBIN params, but just in case...
                        uv_scale_node = self._new_tex_scale_node(sampler.uv_scale, tex_image_node.location.y)
                    self.link(uv_node.outputs["UV"], uv_scale_node.inputs[0])
                    self.link(uv_scale_node.outputs["Vector"], tex_image_node.inputs["Vector"])
                else:
                    self.link(uv_node.outputs["UV"], tex_image_node.inputs["Vector"])

        # Finally, add unrecognized samplers.
        matdef_sampler_names = {sampler.name for sampler in self.matdef.samplers}
        for sampler_name, texture_stem in self.sampler_texture_stems.items():
            if sampler_name in matdef_sampler_names:
                continue
            self.tex_y -= 100  # space these out a bit more
            bl_image = self.get_sampler_bl_image(sampler_name)
            tex_image_node = self._new_tex_image_node(
                name=sampler_name, image=bl_image, label=sampler_name, hide=bl_image is None
            )
            self.tex_image_nodes[sampler_name] = tex_image_node

    def _initialize_node_tree(self):
        # Remove all node links.
        self.tree.links.clear()
        # Remove all nodes except Material Output.
        for node in tuple(self.tree.nodes):
            if node.name != "Material Output":
                self.tree.nodes.remove(self.tree.nodes[node.name])

        # Build vertex color nodes.
        self.vertex_colors_nodes = [
            self._new_vertex_colors_attr_node(i) for i in range(self.vertex_color_count)
        ]

        try:
            self.build_shader_uv_texture_nodes()
        except KeyError as ex:
            raise MaterialImportError(
                f"Could not build UV Map and Texture nodes for material '{self.matdef.name}' with shader "
                f"'{self.matdef.shader_stem}'. Error:\n    {ex}"
            )

    def _mix_value_nodes(
        self,
        input_1: NodeSocket,
        input_2: NodeSocket,
        node_y: float,
        mix_fac_input: NodeSocket | float = 0.5,
        mix_data_type: str = "VECTOR"
    ) -> bpy.types.ShaderNodeMix:
        mix_node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMix,
            (self.POST_TEX_X, node_y),
            inputs={
                "Factor": mix_fac_input,
                "A": input_1,
                "B": input_2,
            },
            data_type=mix_data_type,
        )

        return mix_node

    def _get_mixed_texture_color(self, pattern: str, mix_fac_input: NodeSocket | float = 0.5) -> NodeSocket | None:
        """Searches the `MatDef` for samplers that match the pattern, and returns a single socket output for it.

        If there are two or more samplers, it creates the necessary nodes to combine the first two, then returns the
        combined output. Other samplers are ignored.

        Returns `None` if pattern is not found or handled, or no sampler images are defined.
        """
        matches = self.matdef.get_matching_samplers(re.compile(pattern), match_alias=True)
        if len(matches) >= 2:
            if len(matches) >= 3:
                self.operator.warning(
                    f"Found {len(matches)} samplers matching pattern '{pattern}' in material "
                    f"'{self.matdef.name}'. Only the first two will be mixed."
                )

            tex_node1 = self.tex_image_nodes.get(matches[0][1].alias)
            if not tex_node1:
                self.operator.warning(f"Sampler '{matches[0][1].alias}' found but no such texture node exists.")
                return None
            tex_node2 = self.tex_image_nodes.get(matches[1][1].alias)
            if not tex_node2:
                self.operator.warning(f"Sampler '{matches[1][1].alias}' found but no such texture node exists.")
                return None

            if not tex_node1.image and not tex_node2.image:
                # Standard case: no images are defined in sampler slots.
                return None

            return self._mix_value_nodes(
                tex_node1.outputs["Color"],
                tex_node2.outputs["Color"],
                tex_node1.location[1],
                mix_fac_input,
                "RGBA",
            ).outputs["Result"]

        elif len(matches) == 1:
            match = self.tex_image_nodes.get(matches[0][1].alias, None)
            if not match:
                self.operator.warning(f"Sampler '{matches[0][1].alias}' found but no such texture node exists.")
                return None
            if not match.image:
                # Standard case: no image is defined in sampler slot.
                return None
            return match.outputs["Color"]

        # No color textures found.
        return None

    def _get_mixed_texture_normals(
        self, pattern: str, mix_fac_input: NodeSocket | float = 0.5,
    ) -> tuple[NodeSocket | None, NodeSocket | None]:
        """Searches the `MatDef` for samplers that match the pattern, and returns a single socket output for it.

        Texture colors are processed as normals, appropriate to the game.

        If there are two or more samplers, it creates the necessary nodes to combine the first two, then returns the
        combined output. Other samplers are ignored. Also returns combined blue passthru if found.

        Returns `None` if pattern is not found or handled.

        TODO: Combine up to 8 detail normals in Elden Ring...
        """
        matches = self.matdef.get_matching_samplers(re.compile(pattern), match_alias=True)
        if len(matches) >= 2:
            if len(matches) >= 3:
                self.operator.warning(
                    f"Found {len(matches)} samplers matching pattern '{pattern}' in material "
                    f"'{self.matdef.name}'. Only the first two will be mixed."
                )

            tex_node1 = self.tex_image_nodes.get(matches[0][1].alias)
            if not tex_node1:
                self.operator.warning(f"Sampler '{matches[0][1].alias}' found but no such texture node exists.")
                return None, None
            tex_node2 = self.tex_image_nodes.get(matches[1][1].alias)
            if not tex_node2:
                self.operator.warning(f"Sampler '{matches[1][1].alias}' found but no such texture node exists.")
                return None, None

            if not tex_node1.image and not tex_node2.image:
                # Standard case: no images are defined in sampler slots.
                return None, None

            normal_map_node1, blue_passthru1 = self._normal_tex_to_normal_input(
                y=tex_node1.location[1],
                color_input_from=tex_node1.outputs["Color"],
                normal_output_to=None,
                uv_layer_name=matches[0][1].uv_layer_name
            )
            normal_map_node2, blue_passthru2 = self._normal_tex_to_normal_input(
                y=tex_node2.location[1],
                color_input_from=tex_node2.outputs["Color"],
                normal_output_to=None,
                uv_layer_name=matches[1][1].uv_layer_name
            )

            normal_socket = self._mix_value_nodes(
                normal_map_node1.outputs["Normal"],
                normal_map_node2.outputs["Normal"],
                tex_node1.location[1],
                mix_fac_input,
                "VECTOR",
            ).outputs["Result"]

            if blue_passthru1 and blue_passthru2:
                blue_passthru_socket = self._mix_value_nodes(
                    blue_passthru1,
                    blue_passthru2,
                    tex_node1.location[1] - 30,
                    mix_fac_input,
                    "FLOAT",
                ).outputs["Result"]
            else:
                blue_passthru_socket = None

            return normal_socket, blue_passthru_socket

        elif len(matches) == 1:
            match = self.tex_image_nodes.get(matches[0][1].alias)
            if not match:
                self.operator.warning(f"Sampler '{matches[0][1].alias}' found but no such texture node exists.")
                return None, None
            if not match.image:
                # Standard case: no image is defined in sampler slot.
                return None, None

            normal_map_node, blue_passthru = self._normal_tex_to_normal_input(
                y=match.location[1],
                color_input_from=match.outputs["Color"],
                normal_output_to=None,
                uv_layer_name=matches[0][1].uv_layer_name
            )
            return normal_map_node.outputs["Normal"], blue_passthru
        else:
            # No matches found. We supply a default normal map for normals only, using 'UVTexture0'.
            normal_map_node = self._new_normal_map_node(
                "UVTexture0",
                self.mix_y,
                strength=1.0
            )
            normal_map_node.hide = True
            normal_map_node.inputs["Color"].default_value = (0.5, 0.5, 1, 1)
            return normal_map_node.outputs["Normal"], None

    def _get_mixed_texture_alpha(
        self,
        pattern: str,
        mix_fac_input: NodeSocket | float = 0.5,
        only_if: bool = True,
        max_sampler_count: int = 2,
    ) -> NodeSocket | None:
        """Searches the `MatDef` for samplers that match the pattern, and returns a single socket output for it.

        Only texture alpha is used.

        If there are two or more samplers, it creates the necessary nodes to combine the first two, then returns the
        combined output. Other samplers are ignored.

        Returns `None` if pattern is not found or handled or if `only_if` is True (to ease usage in dictionaries).
        """
        if not only_if:
            return None

        matches = self.matdef.get_matching_samplers(re.compile(pattern), match_alias=True)

        if len(matches) > max_sampler_count:
            self.operator.warning(
                f"Found {len(matches)} samplers matching pattern '{pattern}' in material "
                f"'{self.matdef.name}'. Only the first {max_sampler_count} will be mixed."
            )
            matches = matches[:max_sampler_count]
        elif len(matches) == 1:
            match = self.tex_image_nodes.get(matches[0][1].alias)
            if not match:
                self.operator.warning(f"Sampler '{matches[0][1].alias}' found but no such texture node exists.")
                return None
            if not match.image:
                return None
            return match.outputs["Alpha"]
        elif not matches:
            # No matches.
            return None

        tex_node1 = self.tex_image_nodes.get(matches[0][1].alias)
        if not tex_node1:
            self.operator.warning(f"Sampler '{matches[0][1].alias}' found but no such texture node exists.")
            return None
        tex_node2 = self.tex_image_nodes.get(matches[1][1].alias)
        if not tex_node2:
            self.operator.warning(f"Sampler '{matches[1][1].alias}' found but no such texture node exists.")
            return None

        if not tex_node1.image and not tex_node2.image:
            # Standard case: no images are defined in sampler slots.
            return None

        return self._mix_value_nodes(
            tex_node1.outputs["Alpha"],
            tex_node2.outputs["Alpha"],
            tex_node1.location[1] - 50,
            mix_fac_input,
            "FLOAT",
        ).outputs["Result"]

    def get_sampler_bl_image(self, sampler_name: str) -> bpy.types.Image | None:
        """All Blender Images from textures (cached or DDS) are lower-case names. FLVER paths are not case-sensitive."""
        texture_stem = self.sampler_texture_stems[sampler_name].lower()
        if not texture_stem:
            # No texture given in MATBIN or FLVER.
            return None
        # Search for Blender image with no extension, TGA, PNG, or DDS, in that order of preference.
        return find_or_create_image(self.operator, self.context, texture_stem)

    # region Texture Input Methods

    def _normal_tex_to_normal_input(
        self,
        y: float,
        color_input_from: NodeSocket | None,
        normal_output_to: NodeSocket | None,
        uv_layer_name: str,
    ) -> tuple[bpy.types.ShaderNodeNormalMap, bpy.types.NodeSocket | None]:
        """Create a node group that processes input normal map colors (for given game) to Blender normal colors.

        Blender expects red to be the X component (right positive), green to be the Y component (up positive), and blue
        to be the Z component. It also expects the color range [0, 1] to actually represent the normal range [-1, 1],
        i.e. uses a full spherical mapping.

        Most FromSoft games use standard DX format RGB normal maps. We only need to flip the G channel to convert to
        Blender's expected OpenGL format. DSR uses a hemispherical RG normal map with B implicit from normalization
        (given convexity). We need to invert the G channel and compute the B channel to convert to the OpenGL format.

        Elden Ring uses RG in the same way as DSR, but also includes a B channel that encodes shininess.

        As the resulting normals need to be fed into a Normal Map node with a specific UV Map name, this has to be done
        outside the bundled shader node groups.
        """
        if self.USES_RG_NORMALS:
            process_normals_node = new_soulstruct_node_group(
                self.tree,
                SoulstructNodeGroups.ProcessRGNormals,
                location=(self.POST_TEX_X, y),
                inputs={
                    "Normal Map": color_input_from,
                },
            )
            color_input_from = process_normals_node.outputs["Blender RGB Normal Map"]
            blue_passthru = process_normals_node.outputs["Blue Passthru"]
        else:
            blue_passthru = None

        # Create normal map node and link processing group output to it, and output normal map node to BSDF.
        normal_map_node = self._new_normal_map_node(
            uv_layer_name,
            y - 120,
            strength=1.0,
            inputs={"Color": color_input_from,},
            outputs={"Normal": normal_output_to,},
        )
        normal_map_node.hide = True

        return normal_map_node, blue_passthru

    # endregion

    # region Builder Methods

    @tp.overload
    def get_param(self, param_name: str, default: bool) -> bool:
        ...

    @tp.overload
    def get_param(self, param_name: str, default: int) -> int:
        ...

    @tp.overload
    def get_param(self, param_name: str, default: tuple[int, int]) -> tuple[int, int]:
        ...

    @tp.overload
    def get_param(self, param_name: str, default: float) -> float:
        ...

    @tp.overload
    def get_param(self, param_name: str, default: tuple[float, float]) -> tuple[float, float]:
        ...

    @tp.overload
    def get_param(
        self, param_name: str, default: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        ...

    @tp.overload
    def get_param(
        self, param_name: str, default: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        ...

    @tp.overload
    def get_param(
        self, param_name: str, default: tuple[float, float, float, float, float]
    ) -> tuple[float, float, float, float, float]:
        ...

    def get_param(self, param_name: str, default=None):
        """Get param from either `MTD` or `MATBIN` depending on game.

        We handle game subclasses here to use the overloads above.
        """
        if isinstance(self.matdef, ERMatDef):
            if not self.matdef.matbin:
                raise ValueError(f"MatDef {self.matdef.name} does not have a MATBIN attached.")
            return self.matdef.matbin.get_param(param_name, default)

        if not self.matdef.mtd:
            raise ValueError(f"MatDef {self.matdef.name} does not have an MTD attached.")
        return self.matdef.mtd.get_param(param_name, default)

    def link(self, node_output: NodeSocket, node_input: NodeSocket) -> bpy.types.NodeLink:
        return self.tree.links.new(node_output, node_input)

    @property
    def output_surface(self) -> NodeSocket:
        return self.output.inputs["Surface"]
    
    @property
    def output_volume(self) -> NodeSocket:
        return self.output.inputs["Volume"]

    @property
    def output_displacement(self) -> NodeSocket:
        return self.output.inputs["Displacement"]

    def _new_vertex_colors_attr_node(self, index: int) -> bpy.types.Node:
        """Create an Attribute node using 'VertexColors{index}'."""
        return new_shader_node(
            self.tree,
            bpy.types.ShaderNodeAttribute,
            location=(self.POST_TEX_X, 1200 + index * 200),
            name=f"VertexColors{index}",
            attribute_name=f"VertexColors{index}",
        )

    def _new_uv_map_node(self, uv_map_name: str) -> bpy.types.ShaderNodeUVMap:
        """Create a UV Map node for the given UV layer name."""
        uv_map_node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeUVMap,
            location=(self.UV_X, self.uv_y),
            name=uv_map_name,
            label=uv_map_name,
            uv_map=uv_map_name,
        )
        self.uv_y -= 1000
        return uv_map_node

    def _new_tex_scale_node(self, scale: Vector2, node_y: float):
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeVectorMath,
            location=(self.SCALE_X, node_y),
            operation="MULTIPLY",
            label="UV Scale",
        )
        node.inputs[1].default_value = [scale.x, scale.y, 1.0]
        return node

    def _new_normal_combine_node(
        self,
        node_y: float,
        inputs: dict[str, tp.Any] = None,
        outputs: dict[str, tp.Any] = None,
    ):
        return new_soulstruct_node_group(
            self.tree,
            SoulstructNodeGroups.CombineDetail,
            location=(self.POST_TEX_X, node_y),
            inputs=inputs,
            outputs=outputs,
        )

    def _new_tex_image_node(
        self, name: str, image: bpy.types.Image | None, label: str = None, hide=False
    ) -> bpy.types.ShaderNodeTexImage:
        node = new_shader_node(
            self.tree,
            bpy.types.ShaderNodeTexImage,
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
        # noinspection PyTypeChecker
        return node

    def _new_normal_map_node(
        self,
        uv_map_name: str,
        location_y: float,
        strength=1.0,
        inputs: dict[str | int, tp.Any] = None,
        outputs: dict[str | int, tp.Any] = None,
    ) -> bpy.types.ShaderNodeNormalMap:
        return new_shader_node(
            self.tree,
            bpy.types.ShaderNodeNormalMap,
            location=(self.POST_TEX_X, location_y),
            space="TANGENT",
            convention="DIRECTX",  # added in Blender 5.1
            uv_map=uv_map_name,
            inputs=(inputs or {}) | {"Strength": strength},
            outputs=outputs,
        )

    def _new_bsdf_shader_node_group(
        self,
        node_group: SoulstructNodeGroups,
        inputs: dict[str, tp.Any] = None,
        outputs: dict[str, tp.Any] = None,
    ) -> bpy.types.ShaderNodeGroup:
        """Create a new `ShaderNodeGroup` of the given name type, or import it from the packaged blend file.

        Positions group node at the current BSDF_X and bsdf_y, and decrements bsdf_y by 1000.
        """
        node = new_soulstruct_node_group(
            self.tree,
            node_group,
            location=(self.BSDF_X, self.bsdf_y),
            inputs=inputs,
            outputs=outputs,
        )
        self.bsdf_y -= 1000
        return node

    # endregion
