import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShapeKeyBezierPoint(bpy_struct):
    """Point in a shape key for Bézier curves"""

    co: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    handle_left: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    handle_right: mathutils.Vector
    """ 

    :type: mathutils.Vector
    """

    radius: float
    """ Radius for beveling

    :type: float
    """

    tilt: float
    """ Tilt in 3D View

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
