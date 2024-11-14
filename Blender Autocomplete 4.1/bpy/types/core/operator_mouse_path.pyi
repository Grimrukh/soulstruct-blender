import typing
import collections.abc
import mathutils
from .struct import Struct
from .property_group import PropertyGroup
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class OperatorMousePath(PropertyGroup, bpy_struct):
    """Mouse path values for operators that record such paths"""

    loc: mathutils.Vector
    """ Mouse location

    :type: mathutils.Vector
    """

    time: float
    """ Time of mouse location

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
