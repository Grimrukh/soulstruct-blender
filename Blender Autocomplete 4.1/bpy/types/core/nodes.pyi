import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .node import Node

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Nodes(bpy_prop_collection[Node], bpy_struct):
    """Collection of Nodes"""

    active: Node | None
    """ Active node in this tree

    :type: Node | None
    """

    def new(self, type: str | typing.Any) -> Node:
        """Add a node to this node tree

        :param type: Type, Type of node to add (Warning: should be same as node.bl_idname, not node.type!)
        :type type: str | typing.Any
        :return: New node
        :rtype: Node
        """
        ...

    def remove(self, node: Node):
        """Remove a node from this node tree

        :param node: The node to remove
        :type node: Node
        """
        ...

    def clear(self):
        """Remove all nodes from this node tree"""
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
