import typing
import collections.abc
import mathutils
from .struct import Struct
from .shader_node import ShaderNode
from .bpy_struct import bpy_struct
from .id import ID
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShaderNodeTree(NodeTree, ID, bpy_struct):
    """Node tree consisting of linked nodes used for materials (and other shading data-blocks)"""

    def get_output_node(self, target: str | None) -> ShaderNode:
        """Return active shader output node for the specified target

                :param target: Target

        ALL
        All -- Use shaders for all renderers and viewports, unless there exists a more specific output.

        EEVEE
        EEVEE -- Use shaders for EEVEE renderer.

        CYCLES
        Cycles -- Use shaders for Cycles renderer.
                :type target: str | None
                :return: Node
                :rtype: ShaderNode
        """
        ...

    @classmethod
    def bl_rna_get_subclass(cls, id: str | None, default=None) -> Struct:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The RNA type or default when not found.
        :rtype: Struct
        """
        ...

    @classmethod
    def bl_rna_get_subclass_py(cls, id: str | None, default=None) -> typing.Any:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The class or default when not found.
        :rtype: typing.Any
        """
        ...
