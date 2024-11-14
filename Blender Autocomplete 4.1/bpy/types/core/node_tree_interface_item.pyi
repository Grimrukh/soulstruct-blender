import typing
import collections.abc
import mathutils
from .struct import Struct
from .node_tree_interface_panel import NodeTreeInterfacePanel
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeTreeInterfaceItem(bpy_struct):
    """Item in a node tree interface"""

    index: int
    """ Global index of the item among all items in the interface

    :type: int
    """

    item_type: str
    """ Type of interface item

    :type: str
    """

    parent: NodeTreeInterfacePanel
    """ Panel that contains the item

    :type: NodeTreeInterfacePanel
    """

    position: int
    """ Position of the item in its parent panel

    :type: int
    """

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
