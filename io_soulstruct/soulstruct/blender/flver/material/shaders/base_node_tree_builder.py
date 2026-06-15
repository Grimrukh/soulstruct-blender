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

from soulstruct.base.models.shaders import MatDef, MatDefSampler
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

            bl_image = self._get_sampler_bl_image(sampler.name)
            tex_image_node = self._new_tex_image_node(
                name=node_name, image=bl_image, label=node_label, hide=bl_image is None
            )

            # Dictionary keys are sampler aliases, not game-specific sampler names (though alias may fall back to that).
            self.tex_image_nodes[node_label] = tex_image_node

            # We take this opportunity to change the Color Space of non-Albedo textures to 'Non-Color'.
            # NOTE: If the texture is used inconsistently across materials, this could change repeatedly.
            if bl_image:
                if "Albedo" not in node_label and "Diffuse" not in node_label and "Lightmap" not in node_label:
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
            bl_image = self._get_sampler_bl_image(sampler_name)
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

    # region Mix / Resolve Helpers

    @property
    def _vc_alpha(self) -> NodeSocket | float:
        """Vertex colors alpha output from the first vertex color node, or ``1.0`` if none exist."""
        if self.vertex_colors_nodes:
            return self.vertex_colors_nodes[0].outputs["Alpha"]
        return 1.0

    def _find_matching_tex_nodes(
        self,
        pattern: str,
        max_count: int = 2,
    ) -> list[tuple[MatDefSampler, bpy.types.ShaderNodeTexImage]]:
        """Find sampler tex-image nodes whose alias matches *pattern* (regex).

        Returns up to *max_count* ``(sampler, tex_node)`` pairs.  Tex nodes whose
        ``.image`` is ``None`` are still included — callers decide how to handle
        missing images.  Warns and skips samplers for which no Blender texture node
        was created.
        """
        from soulstruct.base.models.shaders import MatDefSampler  # noqa – avoid circular at module level

        matches = self.matdef.get_matching_samplers(re.compile(pattern), match_alias=True)
        if len(matches) > max_count:
            self.operator.debug(
                f"Found {len(matches)} samplers matching pattern '{pattern}' in material "
                f"'{self.matdef.name}'. Only the first {max_count} will be used."
            )
            matches = matches[:max_count]

        results: list[tuple[MatDefSampler, bpy.types.ShaderNodeTexImage]] = []
        for _, sampler in matches:
            tex_node = self.tex_image_nodes.get(sampler.alias)
            if not tex_node:
                self.operator.warning(
                    f"Sampler '{sampler.alias}' found but no such texture node exists."
                )
                continue
            results.append((sampler, tex_node))
        return results

    @staticmethod
    def _adjust_mix_fac_for_images(
        tex_a: bpy.types.ShaderNodeTexImage,
        tex_b: bpy.types.ShaderNodeTexImage,
        mix_fac: NodeSocket | float,
    ) -> NodeSocket | float | None:
        """Return an adjusted mix factor based on which tex nodes have images.

        Returns ``None`` when *both* textures are missing (caller should bail).
        """
        if not tex_a.image and not tex_b.image:
            return None
        if not tex_a.image:
            return 1.0
        if not tex_b.image:
            return 0.0
        return mix_fac

    def _mix_value_nodes(
        self,
        input_a: NodeSocket,
        input_b: NodeSocket,
        node_y: float,
        mix_fac: NodeSocket | float = 0.5,
        data_type: str = "VECTOR",
    ) -> bpy.types.ShaderNodeMix:
        """Create a ``ShaderNodeMix`` that blends *input_a* / *input_b* and return the **node**."""
        return new_shader_node(
            self.tree,
            bpy.types.ShaderNodeMix,
            (self.POST_TEX_X, node_y),
            inputs={"Factor": mix_fac, "A": input_a, "B": input_b},
            data_type=data_type,
        )

    def _mix_sockets(
        self,
        input_a: NodeSocket,
        input_b: NodeSocket,
        node_y: float,
        mix_fac: NodeSocket | float = 0.5,
        data_type: str = "VECTOR",
    ) -> NodeSocket:
        """Create a ``ShaderNodeMix`` and return its **Result** output socket directly."""
        return self._mix_value_nodes(input_a, input_b, node_y, mix_fac, data_type).outputs["Result"]

    def _chain_mix_sockets(
        self,
        base: NodeSocket | None,
        layers: list[tuple[NodeSocket | None, NodeSocket | float]],
        node_y: float,
        data_type: str = "VECTOR",
        y_step: float = -40,
    ) -> NodeSocket | None:
        """Chain-mix *base* with each ``(overlay, factor)`` in *layers*, skipping ``None`` overlays.

        If *base* is ``None`` the first non-``None`` overlay replaces it.  Returns
        ``None`` only when *base* and every overlay are all ``None``.

        Useful for blending an arbitrary number of detail/secondary textures into a
        primary channel without per-step ``None`` boilerplate in callers.
        """
        current = base
        y = node_y
        for overlay, fac in layers:
            if overlay is None:
                continue
            if current is None:
                current = overlay
            else:
                current = self._mix_sockets(current, overlay, y, fac, data_type)
                y += y_step
        return current

    def _masked_blend_sockets(
        self,
        base: NodeSocket,
        overlay: NodeSocket,
        node_y: float,
        mask_fac: NodeSocket | float,
        uv_fac: NodeSocket | float,
        data_type: str = "VECTOR",
    ) -> NodeSocket:
        """Two-step masked blend used by multi-blend shaders.

        Step 1 — **mask mix**:  ``Mix(fac=mask, A=overlay, B=base)``
            *mask* = 1 → base, *mask* = 0 → overlay.
        Step 2 — **UV override**: ``Mix(fac=uv, A=step1, B=base)``
            *uv* = 0 → step-1 result (blend applied), *uv* = 1 → base (blend ignored).

        Returns the final blended socket.
        """
        mask_blended = self._mix_sockets(overlay, base, node_y, mask_fac, data_type)
        return self._mix_sockets(mask_blended, base, node_y, uv_fac, data_type)

    def _process_normal_tex(
        self,
        tex_node: bpy.types.ShaderNodeTexImage,
        uv_layer_name: str,
    ) -> tuple[NodeSocket, NodeSocket | None]:
        """Process a single normal-map texture through RG-normal processing and a Normal Map node.

        Returns ``(normal_socket, blue_passthru_socket)``.
        """
        normal_map_node, blue_passthru = self._normal_tex_to_normal_input(
            y=tex_node.location[1],
            color_input_from=tex_node.outputs["Color"],
            normal_output_to=None,
            uv_layer_name=uv_layer_name,
        )
        return normal_map_node.outputs["Normal"], blue_passthru

    def _make_default_normal_socket(self) -> tuple[NodeSocket, None]:
        """Create a flat (default) Normal Map node on ``UVTexture0``.

        Used as fallback when no normal-map samplers are found.
        """
        normal_map_node = self._new_normal_map_node("UVTexture0", self.mix_y, strength=1.0)
        normal_map_node.hide = True
        normal_map_node.inputs["Color"].default_value = (0.5, 0.5, 1, 1)
        return normal_map_node.outputs["Normal"], None

    # endregion

    # region Mixed-Texture Resolution

    def _get_mixed_texture_color(
        self,
        pattern: str,
        mix_fac_input: NodeSocket | float = 0.5,
    ) -> NodeSocket | None:
        """Find samplers matching *pattern* and return a single ``Color`` output socket.

        Mixes the first two matches when both are present, adjusting the factor when one
        is missing.  Returns ``None`` if no images are defined.
        """
        found = self._find_matching_tex_nodes(pattern)
        if not found:
            return None
        if len(found) == 1:
            _, tex_node = found[0]
            return tex_node.outputs["Color"] if tex_node.image else None

        (_, tex_a), (_, tex_b) = found[0], found[1]
        fac = self._adjust_mix_fac_for_images(tex_a, tex_b, mix_fac_input)
        if fac is None:
            return None
        return self._mix_sockets(
            tex_a.outputs["Color"], tex_b.outputs["Color"], tex_a.location[1], fac, "RGBA",
        )

    def _get_mixed_texture_normals(
        self,
        pattern: str,
        mix_fac_input: NodeSocket | float = 0.5,
    ) -> tuple[NodeSocket | None, NodeSocket | None]:
        """Find normal-map samplers matching *pattern*, process them, and return mixed outputs.

        Each texture is processed through RG-normal handling (game-dependent) and a
        Normal Map node.  Returns ``(normal_socket, blue_passthru_socket)``.  Falls back
        to a flat default normal when no matches exist.
        """
        found = self._find_matching_tex_nodes(pattern)
        if not found:
            return self._make_default_normal_socket()

        if len(found) == 1:
            sampler, tex_node = found[0]
            if not tex_node.image:
                return None, None
            return self._process_normal_tex(tex_node, sampler.uv_layer_name)

        (sampler_a, tex_a), (sampler_b, tex_b) = found[0], found[1]
        fac = self._adjust_mix_fac_for_images(tex_a, tex_b, mix_fac_input)
        if fac is None:
            return None, None

        normal_a, blue_a = self._process_normal_tex(tex_a, sampler_a.uv_layer_name)
        normal_b, blue_b = self._process_normal_tex(tex_b, sampler_b.uv_layer_name)

        normal_socket = self._mix_sockets(normal_a, normal_b, tex_a.location[1], fac, "VECTOR")

        if blue_a and blue_b:
            blue_socket = self._mix_sockets(blue_a, blue_b, tex_a.location[1] - 30, fac, "FLOAT")
        else:
            blue_socket = blue_a or blue_b

        return normal_socket, blue_socket

    def _get_mixed_texture_alpha(
        self,
        pattern: str,
        mix_fac_input: NodeSocket | float = 0.5,
        only_if: bool = True,
        max_sampler_count: int = 2,
    ) -> NodeSocket | None:
        """Find samplers matching *pattern* and return a single ``Alpha`` output socket.

        Mixes the first *max_sampler_count* matches.  Returns ``None`` when *only_if* is
        ``False`` (convenience for conditional dict construction).
        """
        if not only_if:
            return None

        found = self._find_matching_tex_nodes(pattern, max_count=max_sampler_count)
        if not found:
            return None
        if len(found) == 1:
            _, tex_node = found[0]
            return tex_node.outputs["Alpha"] if tex_node.image else None

        (_, tex_a), (_, tex_b) = found[0], found[1]
        fac = self._adjust_mix_fac_for_images(tex_a, tex_b, mix_fac_input)
        if fac is None:
            return None
        return self._mix_sockets(
            tex_a.outputs["Alpha"], tex_b.outputs["Alpha"], tex_a.location[1] - 50, fac, "FLOAT",
        )

    def _get_sampler_bl_image(self, sampler_name: str) -> bpy.types.Image | None:
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

    # endregion

    # region Node Creation

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
        inputs: dict[str, tp.Any] | None = None,
        outputs: dict[str, tp.Any] | None = None,
    ):
        return new_soulstruct_node_group(
            self.tree,
            SoulstructNodeGroups.CombineDetail,
            location=(self.POST_TEX_X, node_y),
            inputs=inputs,
            outputs=outputs,
        )

    def _new_tex_image_node(
        self, name: str, image: bpy.types.Image | None, label: str | None = None, hide: bool = False
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
        inputs: dict[str | int, tp.Any] | None = None,
        outputs: dict[str | int, tp.Any] | None = None,
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
        inputs: dict[str, tp.Any] | None = None,
        outputs: dict[str, tp.Any] | None = None,
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
