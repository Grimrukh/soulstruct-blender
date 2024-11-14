import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class TriangulateModifier(Modifier, bpy_struct):
    """Triangulate Mesh"""

    keep_custom_normals: bool
    """ Try to preserve custom normals.
Warning: Depending on chosen triangulation method, shading may not be fully preserved, "Fixed" method usually gives the best result here

    :type: bool
    """

    min_vertices: int
    """ Triangulate only polygons with vertex count greater than or equal to this number

    :type: int
    """

    ngon_method: str
    """ Method for splitting the n-gons into triangles

    :type: str
    """

    quad_method: str
    """ Method for splitting the quads into triangles

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
