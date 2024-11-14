import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .property import Property

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IntProperty(Property, bpy_struct):
    """RNA integer number property definition"""

    array_dimensions: bpy_prop_array[int]
    """ Length of each dimension of the array

    :type: bpy_prop_array[int]
    """

    array_length: int
    """ Maximum length of the array, 0 means unlimited

    :type: int
    """

    default: int
    """ Default value for this number

    :type: int
    """

    default_array: bpy_prop_array[int]
    """ Default value for this array

    :type: bpy_prop_array[int]
    """

    hard_max: int
    """ Maximum value used by buttons

    :type: int
    """

    hard_min: int
    """ Minimum value used by buttons

    :type: int
    """

    is_array: bool
    """ 

    :type: bool
    """

    soft_max: int
    """ Maximum value used by buttons

    :type: int
    """

    soft_min: int
    """ Minimum value used by buttons

    :type: int
    """

    step: int
    """ Step size used by number buttons, for floats 1/100th of the step size

    :type: int
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
