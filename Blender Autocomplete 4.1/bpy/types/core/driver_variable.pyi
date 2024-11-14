import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .driver_target import DriverTarget

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DriverVariable(bpy_struct):
    """Variable from some source/target for driver relationship"""

    is_name_valid: bool
    """ Is this a valid name for a driver variable

    :type: bool
    """

    name: str
    """ Name to use in scripted expressions/functions (no spaces or dots are allowed, and must start with a letter)

    :type: str
    """

    targets: bpy_prop_collection[DriverTarget]
    """ Sources of input data for evaluating this variable

    :type: bpy_prop_collection[DriverTarget]
    """

    type: str
    """ Driver variable type

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
