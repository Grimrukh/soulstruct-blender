import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FollowPathConstraint(Constraint, bpy_struct):
    """Lock motion to the target path"""

    forward_axis: str
    """ Axis that points forward along the path

    :type: str
    """

    offset: float
    """ Offset from the position corresponding to the time frame

    :type: float
    """

    offset_factor: float
    """ Percentage value defining target position along length of curve

    :type: float
    """

    target: Object
    """ Target Curve object

    :type: Object
    """

    up_axis: str
    """ Axis that points upward

    :type: str
    """

    use_curve_follow: bool
    """ Object will follow the heading and banking of the curve

    :type: bool
    """

    use_curve_radius: bool
    """ Object is scaled by the curve radius

    :type: bool
    """

    use_fixed_location: bool
    """ Object will stay locked to a single point somewhere along the length of the curve regardless of time

    :type: bool
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
