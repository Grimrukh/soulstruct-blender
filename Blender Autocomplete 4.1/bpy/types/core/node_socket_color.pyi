import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .node_socket import NodeSocket
from .node_socket_standard import NodeSocketStandard

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeSocketColor(NodeSocketStandard, NodeSocket, bpy_struct):
    """RGBA color socket of a node"""

    default_value: bpy_prop_array[float]
    """ Input value used for unconnected socket

    :type: bpy_prop_array[float]
    """

    links: typing.Any
    """ List of node links from or to this socket.(readonly)"""

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
