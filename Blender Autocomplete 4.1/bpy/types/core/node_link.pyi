import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_socket import NodeSocket
from .node import Node

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeLink(bpy_struct):
    """Link between nodes in a node tree"""

    from_node: Node
    """ 

    :type: Node
    """

    from_socket: NodeSocket
    """ 

    :type: NodeSocket
    """

    is_hidden: bool
    """ Link is hidden due to invisible sockets

    :type: bool
    """

    is_muted: bool
    """ Link is muted and can be ignored

    :type: bool
    """

    is_valid: bool
    """ Link is valid

    :type: bool
    """

    multi_input_sort_id: int
    """ Used to sort multiple links coming into the same input. The highest ID is at the top

    :type: int
    """

    to_node: Node
    """ 

    :type: Node
    """

    to_socket: NodeSocket
    """ 

    :type: NodeSocket
    """

    def swap_multi_input_sort_id(self, other: NodeLink):
        """Swap the order of two links connected to the same multi-input socket

        :param other: Other, The other link. Must link to the same multi input socket
        :type other: NodeLink
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
