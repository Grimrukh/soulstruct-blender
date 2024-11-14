import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .node_tree_path import NodeTreePath
from .bpy_struct import bpy_struct
from .node import Node
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceNodeEditorPath(bpy_prop_collection[NodeTreePath], bpy_struct):
    """Get the node tree path as a string"""

    to_string: str
    """ 

    :type: str
    """

    def clear(self):
        """Reset the node tree path"""
        ...

    def start(self, node_tree: NodeTree | None):
        """Set the root node tree

        :param node_tree: Node Tree
        :type node_tree: NodeTree | None
        """
        ...

    def append(self, node_tree: NodeTree | None, node: Node | None = None):
        """Append a node group tree to the path

        :param node_tree: Node Tree, Node tree to append to the node editor path
        :type node_tree: NodeTree | None
        :param node: Node, Group node linking to this node tree
        :type node: Node | None
        """
        ...

    def pop(self):
        """Remove the last node tree from the path"""
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
