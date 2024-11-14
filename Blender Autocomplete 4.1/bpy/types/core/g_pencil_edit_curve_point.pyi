import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GPencilEditCurvePoint(bpy_struct):
    """Bézier curve point with two handles"""

    co: mathutils.Vector
    """ Coordinates of the control point

    :type: mathutils.Vector
    """

    handle_left: mathutils.Vector
    """ Coordinates of the first handle

    :type: mathutils.Vector
    """

    handle_right: mathutils.Vector
    """ Coordinates of the second handle

    :type: mathutils.Vector
    """

    hide: bool
    """ Visibility status

    :type: bool
    """

    point_index: int
    """ Index of the corresponding grease pencil stroke point

    :type: int
    """

    pressure: float
    """ Pressure of the grease pencil stroke point

    :type: float
    """

    select_control_point: bool
    """ Control point selection status

    :type: bool
    """

    select_left_handle: bool
    """ Handle 1 selection status

    :type: bool
    """

    select_right_handle: bool
    """ Handle 2 selection status

    :type: bool
    """

    strength: float
    """ Color intensity (alpha factor) of the grease pencil stroke point

    :type: float
    """

    uv_factor: float
    """ Internal UV factor

    :type: float
    """

    uv_rotation: float
    """ Internal UV factor for dot mode

    :type: float
    """

    vertex_color: bpy_prop_array[float]
    """ Vertex color of the grease pencil stroke point

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
