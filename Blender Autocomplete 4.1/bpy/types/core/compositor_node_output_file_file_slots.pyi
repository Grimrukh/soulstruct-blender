import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_socket import NodeSocket
from .node_output_file_slot_file import NodeOutputFileSlotFile

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CompositorNodeOutputFileFileSlots(
    bpy_prop_collection[NodeOutputFileSlotFile], bpy_struct
):
    """Collection of File Output node slots"""

    def new(self, name: str | typing.Any) -> NodeSocket:
        """Add a file slot to this node

        :param name: Name
        :type name: str | typing.Any
        :return: New socket
        :rtype: NodeSocket
        """
        ...

    def remove(self, socket: NodeSocket | None):
        """Remove a file slot from this node

        :param socket: The socket to remove
        :type socket: NodeSocket | None
        """
        ...

    def clear(self):
        """Remove all file slots from this node"""
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move a file slot to another position

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
