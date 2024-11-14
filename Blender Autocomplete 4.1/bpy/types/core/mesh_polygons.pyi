import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .mesh_polygon import MeshPolygon
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshPolygons(bpy_prop_collection[MeshPolygon], bpy_struct):
    """Collection of mesh polygons"""

    active: int | None
    """ The active face for this mesh

    :type: int | None
    """

    def add(self, count: int | None):
        """add

        :param count: Count, Number of polygons to add
        :type count: int | None
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
