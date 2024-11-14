import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .property import Property

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FloatProperty(Property, bpy_struct):
    """RNA floating-point number (single precision) property definition"""

    array_dimensions: bpy_prop_array[int]
    """ Length of each dimension of the array

    :type: bpy_prop_array[int]
    """

    array_length: int
    """ Maximum length of the array, 0 means unlimited

    :type: int
    """

    default: float
    """ Default value for this number

    :type: float
    """

    default_array: bpy_prop_array[float]
    """ Default value for this array

    :type: bpy_prop_array[float]
    """

    hard_max: float
    """ Maximum value used by buttons

    :type: float
    """

    hard_min: float
    """ Minimum value used by buttons

    :type: float
    """

    is_array: bool
    """ 

    :type: bool
    """

    precision: int
    """ Number of digits after the dot used by buttons. Fraction is automatically hidden for exact integer values of fields with unit 'NONE' or 'TIME' (frame count) and step divisible by 100

    :type: int
    """

    soft_max: float
    """ Maximum value used by buttons

    :type: float
    """

    soft_min: float
    """ Minimum value used by buttons

    :type: float
    """

    step: float
    """ Step size used by number buttons, for floats 1/100th of the step size

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
