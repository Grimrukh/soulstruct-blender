import typing
import collections.abc
import mathutils
from .vertex_group import VertexGroup
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VertexGroups(bpy_prop_collection[VertexGroup], bpy_struct):
    """Collection of vertex groups"""

    active: VertexGroup | None
    """ Vertex groups of the object

    :type: VertexGroup | None
    """

    active_index: int | None
    """ Active index in vertex group array

    :type: int | None
    """

    def new(self, name: str | typing.Any = "Group") -> VertexGroup:
        """Add vertex group to object

        :param name: Vertex group name
        :type name: str | typing.Any
        :return: New vertex group
        :rtype: VertexGroup
        """
        ...

    def remove(self, group: VertexGroup):
        """Delete vertex group from object

        :param group: Vertex group to remove
        :type group: VertexGroup
        """
        ...

    def clear(self):
        """Delete all vertex groups from object"""
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
