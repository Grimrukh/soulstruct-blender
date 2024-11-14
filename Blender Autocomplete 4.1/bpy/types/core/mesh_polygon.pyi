import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MeshPolygon(bpy_struct):
    """Polygon in a Mesh data-block"""

    area: float
    """ Read only area of this face

    :type: float
    """

    center: mathutils.Vector
    """ Center of this face

    :type: mathutils.Vector
    """

    hide: bool
    """ 

    :type: bool
    """

    index: int
    """ Index of this face

    :type: int
    """

    loop_start: int
    """ Index of the first loop of this face

    :type: int
    """

    loop_total: int
    """ Number of loops used by this face

    :type: int
    """

    material_index: int
    """ Material slot index of this face

    :type: int
    """

    normal: mathutils.Vector
    """ Local space unit length normal vector for this face

    :type: mathutils.Vector
    """

    select: bool
    """ 

    :type: bool
    """

    use_freestyle_mark: bool
    """ Face mark for Freestyle line rendering

    :type: bool
    """

    use_smooth: bool
    """ 

    :type: bool
    """

    vertices: bpy_prop_array[int]
    """ Vertex indices

    :type: bpy_prop_array[int]
    """

    edge_keys: typing.Any
    """ (readonly)"""

    loop_indices: typing.Any
    """ (readonly)"""

    def flip(self):
        """Invert winding of this face (flip its normal)"""
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
