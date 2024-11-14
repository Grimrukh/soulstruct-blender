import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SplinePoint(bpy_struct):
    """Spline point without handles"""

    co: mathutils.Vector
    """ Point coordinates

    :type: mathutils.Vector
    """

    hide: bool
    """ Visibility status

    :type: bool
    """

    radius: float
    """ Radius for beveling

    :type: float
    """

    select: bool
    """ Selection status

    :type: bool
    """

    tilt: float
    """ Tilt in 3D View

    :type: float
    """

    weight: float
    """ NURBS weight

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
