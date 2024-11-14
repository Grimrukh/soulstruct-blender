import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BezierSplinePoint(bpy_struct):
    """Bézier curve point with two handles"""

    co: mathutils.Vector
    """ Coordinates of the control point

    :type: mathutils.Vector
    """

    handle_left: mathutils.Vector
    """ Coordinates of the first handle

    :type: mathutils.Vector
    """

    handle_left_type: str
    """ Handle types

    :type: str
    """

    handle_right: mathutils.Vector
    """ Coordinates of the second handle

    :type: mathutils.Vector
    """

    handle_right_type: str
    """ Handle types

    :type: str
    """

    hide: bool
    """ Visibility status

    :type: bool
    """

    radius: float
    """ Radius for beveling

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

    tilt: float
    """ Tilt in 3D View

    :type: float
    """

    weight_softbody: float
    """ Softbody goal weight

    :type: float
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
