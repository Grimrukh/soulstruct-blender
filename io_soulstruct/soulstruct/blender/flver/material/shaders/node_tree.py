"""Simple utility functions for creating and manipulating Blender shader node trees."""
from __future__ import annotations

__all__ = [
    "new_shader_node",
    "new_shader_math_node",
]

import typing as tp

import bpy

from .enums import *

NODE_T = tp.TypeVar("NODE_T", bound=bpy.types.Node)


def new_shader_node(
    tree: bpy.types.NodeTree,
    node_type: type[NODE_T],
    location: tuple[int, int] = None,
    /,
    inputs: dict[str | int, tp.Any] = None,
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
