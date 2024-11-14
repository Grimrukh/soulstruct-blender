import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .mask_parent import MaskParent
from .mask_spline_point_uw import MaskSplinePointUW

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaskSplinePoint(bpy_struct):
    """Single point in spline used for defining mask"""

    co: mathutils.Vector
    """ Coordinates of the control point

    :type: mathutils.Vector
    """

    feather_points: bpy_prop_collection[MaskSplinePointUW]
    """ Points defining feather

    :type: bpy_prop_collection[MaskSplinePointUW]
    """

    handle_left: mathutils.Vector
    """ Coordinates of the first handle

    :type: mathutils.Vector
    """

    handle_left_type: str
    """ Handle type

    :type: str
    """

    handle_right: mathutils.Vector
    """ Coordinates of the second handle

    :type: mathutils.Vector
    """

    handle_right_type: str
    """ Handle type

    :type: str
    """

    handle_type: str
    """ Handle type

    :type: str
    """

    parent: MaskParent
    """ 

    :type: MaskParent
    """

    select: bool
    """ Selection status

    :type: bool
    """

    weight: float
    """ Weight of the point

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
