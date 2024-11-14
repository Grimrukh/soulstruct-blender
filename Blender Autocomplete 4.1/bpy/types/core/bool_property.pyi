import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .property import Property

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoolProperty(Property, bpy_struct):
    """RNA boolean property definition"""

    array_dimensions: bpy_prop_array[int]
    """ Length of each dimension of the array

    :type: bpy_prop_array[int]
    """

    array_length: int
    """ Maximum length of the array, 0 means unlimited

    :type: int
    """

    default: bool
    """ Default value for this number

    :type: bool
    """

    default_array: list[bool]
    """ Default value for this array

    :type: list[bool]
    """

    is_array: bool
    """ 

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
