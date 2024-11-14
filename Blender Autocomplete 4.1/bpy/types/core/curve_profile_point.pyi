import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CurveProfilePoint(bpy_struct):
    """Point of a path used to define a profile"""

    handle_type_1: str
    """ Path interpolation at this point

    :type: str
    """

    handle_type_2: str
    """ Path interpolation at this point

    :type: str
    """

    location: mathutils.Vector
    """ X/Y coordinates of the path point

    :type: mathutils.Vector
    """

    select: bool
    """ Selection state of the path point

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
