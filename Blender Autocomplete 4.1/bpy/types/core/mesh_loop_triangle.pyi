import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshLoopTriangle(bpy_struct):
    """Tessellated triangle in a Mesh data-block"""

    area: float
    """ Area of this triangle

    :type: float
    """

    index: int
    """ Index of this loop triangle

    :type: int
    """

    loops: bpy_prop_array[int]
    """ Indices of mesh loops that make up the triangle

    :type: bpy_prop_array[int]
    """

    material_index: int
    """ Material slot index of this triangle

    :type: int
    """

    normal: mathutils.Vector
    """ Local space unit length normal vector for this triangle

    :type: mathutils.Vector
    """

    polygon_index: int
    """ Index of mesh face that the triangle is a part of

    :type: int
    """

    split_normals: list[list[float]] | tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    """ Local space unit length split normal vectors of the face corners of this triangle

    :type: list[list[float]] | tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    """

    use_smooth: bool
    """ 

    :type: bool
    """

    vertices: bpy_prop_array[int]
    """ Indices of triangle vertices

    :type: bpy_prop_array[int]
    """

    center: typing.Any
    """ The midpoint of the face.(readonly)"""

    edge_keys: typing.Any
    """ (readonly)"""

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
