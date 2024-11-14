import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Keyframe(bpy_struct):
    """Bézier curve point with two handles defining a Keyframe on an F-Curve"""

    amplitude: float
    """ Amount to boost elastic bounces for 'elastic' easing

    :type: float
    """

    back: float
    """ Amount of overshoot for 'back' easing

    :type: float
    """

    co: mathutils.Vector
    """ Coordinates of the control point

    :type: mathutils.Vector
    """

    co_ui: mathutils.Vector
    """ Coordinates of the control point. Note: Changing this value also updates the handles similar to using the graph editor transform operator

    :type: mathutils.Vector
    """

    easing: str
    """ Which ends of the segment between this and the next keyframe easing interpolation is applied to

    :type: str
    """

    handle_left: mathutils.Vector
    """ Coordinates of the left handle (before the control point)

    :type: mathutils.Vector
    """

    handle_left_type: str
    """ Handle types

    :type: str
    """

    handle_right: mathutils.Vector
    """ Coordinates of the right handle (after the control point)

    :type: mathutils.Vector
    """

    handle_right_type: str
    """ Handle types

    :type: str
    """

    interpolation: str
    """ Interpolation method to use for segment of the F-Curve from this Keyframe until the next Keyframe

    :type: str
    """

    period: float
    """ Time between bounces for elastic easing

    :type: float
    """

    select_control_point: bool
    """ Control point selection status

    :type: bool
    """

    select_left_handle: bool
    """ Left handle selection status

    :type: bool
    """

    select_right_handle: bool
    """ Right handle selection status

    :type: bool
    """

    type: str
    """ Type of keyframe (for visual purposes only)

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
