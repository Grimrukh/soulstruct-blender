import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .node_socket import NodeSocket
from .node_link import NodeLink

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class NodeLinks(bpy_prop_collection[NodeLink], bpy_struct):
    """Collection of Node Links"""

    def new(
        self,
        input: NodeSocket,
        output: NodeSocket,
        verify_limits: bool | typing.Any | None = True,
    ) -> NodeLink:
        """Add a node link to this node tree

        :param input: The input socket
        :type input: NodeSocket
        :param output: The output socket
        :type output: NodeSocket
        :param verify_limits: Verify Limits, Remove existing links if connection limit is exceeded
        :type verify_limits: bool | typing.Any | None
        :return: New node link
        :rtype: NodeLink
        """
        ...

    def remove(self, link: NodeLink):
        """remove a node link from the node tree

        :param link: The node link to remove
        :type link: NodeLink
        """
        ...

    def clear(self):
        """remove all node links from the node tree"""
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
