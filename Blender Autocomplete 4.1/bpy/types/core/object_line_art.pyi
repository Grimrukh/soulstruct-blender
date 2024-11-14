import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ObjectLineArt(bpy_struct):
    """Object line art settings"""

    crease_threshold: float
    """ Angles smaller than this will be treated as creases

    :type: float
    """

    intersection_priority: int
    """ The intersection line will be included into the object with the higher intersection priority value

    :type: int
    """

    usage: str
    """ How to use this object in line art calculation

    :type: str
    """

    use_crease_override: bool
    """ Use this object's crease setting to overwrite scene global

    :type: bool
    """

    use_intersection_priority_override: bool
    """ Use this object's intersection priority to override collection setting

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
