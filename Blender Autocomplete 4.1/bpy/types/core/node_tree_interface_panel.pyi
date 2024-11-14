import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_tree_interface_item import NodeTreeInterfaceItem

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeTreeInterfacePanel(NodeTreeInterfaceItem, bpy_struct):
    """Declaration of a node panel"""

    default_closed: bool
    """ Panel is closed by default on new nodes

    :type: bool
    """

    description: str
    """ Panel description

    :type: str
    """

    interface_items: bpy_prop_collection[NodeTreeInterfaceItem]
    """ Items in the node panel

    :type: bpy_prop_collection[NodeTreeInterfaceItem]
    """

    name: str
    """ Panel name

    :type: str
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
