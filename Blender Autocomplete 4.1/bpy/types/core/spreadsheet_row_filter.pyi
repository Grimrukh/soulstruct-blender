import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpreadsheetRowFilter(bpy_struct):
    column_name: str
    """ 

    :type: str
    """

    enabled: bool
    """ 

    :type: bool
    """

    operation: str
    """ 

    :type: str
    """

    show_expanded: bool
    """ 

    :type: bool
    """

    threshold: float
    """ How close float values need to be to be equal

    :type: float
    """

    value_boolean: bool
    """ 

    :type: bool
    """

    value_color: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    value_float: float
    """ 

    :type: float
    """

    value_float2: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    value_float3: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    value_int: int
    """ 

    :type: int
    """

    value_int2: bpy_prop_array[int]
    """ 

    :type: bpy_prop_array[int]
    """

    value_int8: int
    """ 

    :type: int
    """

    value_string: str
    """ 

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
