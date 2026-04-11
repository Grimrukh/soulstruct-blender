"""Simple utility functions for creating and manipulating Blender shader node trees."""

from __future__ import annotations

__all__ = [
    "TEX_SAMPLER_RE",
    "NODE_INPUT_CONSTANT_TYPING",
    "NODE_INPUT_TYPING",
    "new_shader_node",
    "new_shader_math_node",
    "load_soulstruct_node_group",
    "new_soulstruct_node_group",
]

import re
import typing as tp

import bpy

from ....exceptions import MissingSoulstructNodeGroupError
from ....utilities.files import ADDON_PACKAGE_PATH
from .enums import *

NODE_T = tp.TypeVar("NODE_T", bound=bpy.types.Node)

TEX_SAMPLER_RE = re.compile(r"(Main) (\d+) (Albedo|Specular|Shininess|Normal)")

NODE_INPUT_CONSTANT_TYPING = tp.Union[str, int, tuple[int, ...], float, tuple[float, ...]]
NODE_INPUT_TYPING = tp.Union[NODE_INPUT_CONSTANT_TYPING, bpy.types.NodeSocket]


def new_shader_node(
    tree: bpy.types.NodeTree,
    node_type: type[NODE_T],
    location: tuple[float, float] = None,
    /,
    inputs: dict[str | int, NODE_INPUT_TYPING | None] = None,
    outputs: dict[str | int, bpy.types.NodeSocket] = None,
    **kwargs,
) -> NODE_T:
    """Create a new `bpy.types.Node` of the given type."""
    node = tree.nodes.new(node_type.__name__)
    if location is not None:
        node.location = location
    for k, v in kwargs.items():
        setattr(node, k, v)
    if inputs:
        for k, v in inputs.items():
            if v is None:
                continue  # ignore None values
            if isinstance(v, bpy.types.NodeSocket):
                tree.links.new(v, node.inputs[k])
            else:  # assume constant value
                node.inputs[k].default_value = v
    if outputs:
        for k, v in outputs.items():
            if v is None:
                continue  # ignore None values
            tree.links.new(node.outputs[k], v)
    return node


def new_shader_math_node(
    tree: bpy.types.NodeTree,
    operation: MathOperation | str,
    location: tuple[int, int],
    input_0: float | int | bpy.types.NodeSocket = None,
    input_1: float | int | bpy.types.NodeSocket = None,
) -> bpy.types.ShaderNodeMath:
    """Create a new `ShaderNodeMath` node with the given operation and inputs.

    Each input can be a constant `float` or `int` (set as default value) or a `NodeSocket` to be linked.
    """
    node = tree.nodes.new(ShaderNodeType.Math)
    node.operation = str(operation)
    node.location = location

    if isinstance(input_0, bpy.types.NodeSocket):
        tree.links.new(input_0, node.inputs[0])
    elif input_0 is not None:
        node.inputs[0].default_value = input_0

    if isinstance(input_1, bpy.types.NodeSocket):
        tree.links.new(input_1, node.inputs[1])
    elif input_1 is not None:
        node.inputs[1].default_value = input_1

    # noinspection PyTypeChecker
    return node


def load_soulstruct_node_group(node_group: SoulstructNodeGroups) -> None:
    """Tries to add a node group to the open file from the 'Shaders.blend' file, if it is not already added."""
    if node_group.value in bpy.data.node_groups:
        # Already loaded.
        return
    try:
        shaders_blend_path = ADDON_PACKAGE_PATH("Shaders.blend")
        with bpy.data.libraries.load(str(shaders_blend_path)) as (data_from, data_to):
            data_to.node_groups = [node_group.value]
    except Exception:
        raise MissingSoulstructNodeGroupError(
            f"Could not find node group '{node_group.value}' in bundled 'Shaders.blend' file."
        )


def new_soulstruct_node_group(
    tree: bpy.types.NodeTree,
    node_group: SoulstructNodeGroups,
    location: tuple[float, float] = None,
    *,
    inputs: dict[str, NODE_INPUT_TYPING | None] = None,
    outputs: dict[str, bpy.types.NodeSocket] = None,
) -> bpy.types.ShaderNodeGroup:
    """Constructs a shader node group by appending the node group with the specified name to the open Blender scene.

    Inputs given in `node_inputs` are attached (if sockets) or set as default values to the inputs of the node group,
    and any outputs given in `node_outputs` are attached to those sockets. Inputs values can be `None` to streamline
    the construction of the dictionaries, but output values must be NodeSockets.

    To prevent maintenance issues, input/output keys cannot be index integers.
    """

    load_soulstruct_node_group(node_group)

    return new_shader_node(
        tree,
        bpy.types.ShaderNodeGroup,
        location=location,
        inputs=inputs,
        outputs=outputs,
        node_tree=bpy.data.node_groups[node_group.value],
    )
