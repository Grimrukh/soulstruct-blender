import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleKey(bpy_struct):
    """Key location for a particle over time"""

    angular_velocity: mathutils.Vector
    """ Key angular velocity

    :type: mathutils.Vector
    """

    location: mathutils.Vector
    """ Key location

    :type: mathutils.Vector
    """

    rotation: mathutils.Quaternion
    """ Key rotation quaternion

    :type: mathutils.Quaternion
    """

    time: float
    """ Time of key over the simulation

    :type: float
    """

    velocity: mathutils.Vector
    """ Key velocity

    :type: mathutils.Vector
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
