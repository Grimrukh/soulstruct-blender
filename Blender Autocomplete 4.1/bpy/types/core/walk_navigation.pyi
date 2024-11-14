import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class WalkNavigation(bpy_struct):
    """Walk navigation settings"""

    jump_height: float
    """ Maximum height of a jump

    :type: float
    """

    mouse_speed: float
    """ Speed factor for when looking around, high values mean faster mouse movement

    :type: float
    """

    teleport_time: float
    """ Interval of time warp when teleporting in navigation mode

    :type: float
    """

    use_gravity: bool
    """ Walk with gravity, or free navigate

    :type: bool
    """

    use_mouse_reverse: bool
    """ Reverse the vertical movement of the mouse

    :type: bool
    """

    view_height: float
    """ View distance from the floor when walking

    :type: float
    """

    walk_speed: float
    """ Base speed for walking and flying

    :type: float
    """

    walk_speed_factor: float
    """ Multiplication factor when using the fast or slow modifiers

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
