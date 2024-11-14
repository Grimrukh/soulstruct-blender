import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_tree import NodeTree

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataNodeTrees(bpy_prop_collection[NodeTree], bpy_struct):
    """Collection of node trees"""

    def new(self, name: str | typing.Any, type: str | None) -> NodeTree:
        """Add a new node tree to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param type: Type, The type of node_group to add
        :type type: str | None
        :return: New node tree data-block
        :rtype: NodeTree
        """
        ...

    def remove(
        self,
        tree: NodeTree,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a node tree from the current blendfile

        :param tree: Node tree to remove
        :type tree: NodeTree
        :param do_unlink: Unlink all usages of this node tree before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this node tree
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this node tree
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
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
