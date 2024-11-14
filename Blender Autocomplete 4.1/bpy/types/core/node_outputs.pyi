import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_socket import NodeSocket

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeOutputs(bpy_prop_collection[NodeSocket], bpy_struct):
    """Collection of Node Sockets"""

    def new(
        self,
        type: str | typing.Any,
        name: str | typing.Any,
        identifier: str | typing.Any = "",
    ) -> NodeSocket:
        """Add a socket to this node

        :param type: Type, Data type
        :type type: str | typing.Any
        :param name: Name
        :type name: str | typing.Any
        :param identifier: Identifier, Unique socket identifier
        :type identifier: str | typing.Any
        :return: New socket
        :rtype: NodeSocket
        """
        ...

    def remove(self, socket: NodeSocket | None):
        """Remove a socket from this node

        :param socket: The socket to remove
        :type socket: NodeSocket | None
        """
        ...

    def clear(self):
        """Remove all sockets from this node"""
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move a socket to another position

        :param from_index: From Index, Index of the socket to move
        :type from_index: int | None
        :param to_index: To Index, Target index for the socket
        :type to_index: int | None
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
