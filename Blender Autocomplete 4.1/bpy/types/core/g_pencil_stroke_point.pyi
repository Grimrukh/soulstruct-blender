import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilStrokePoint(bpy_struct):
    """Data point for freehand stroke curve"""

    co: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    pressure: float
    """ Pressure of tablet at point when drawing it

    :type: float
    """

    select: bool
    """ Point is selected for viewport editing

    :type: bool
    """

    strength: float
    """ Color intensity (alpha factor)

    :type: float
    """

    time: float
    """ Time relative to stroke start

    :type: float
    """

    uv_factor: float
    """ Internal UV factor

    :type: float
    """

    uv_fill: mathutils.Vector
    """ Internal UV factor for filling

    :type: mathutils.Vector
    """

    uv_rotation: float
    """ Internal UV factor for dot mode

    :type: float
    """

    vertex_color: bpy_prop_array[float]
    """ Color used to mix with point color to get final color

    :type: bpy_prop_array[float]
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
