import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .property_group import PropertyGroup
from .bpy_prop_array import bpy_prop_array
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class PropertyGroupItem(bpy_struct):
    """Property that stores arbitrary, user defined properties"""

    bool: bool
    """ 

    :type: bool
    """

    bool_array: list[bool]
    """ 

    :type: list[bool]
    """

    collection: bpy_prop_collection[PropertyGroup]
    """ 

    :type: bpy_prop_collection[PropertyGroup]
    """

    double: float
    """ 

    :type: float
    """

    double_array: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    enum: str
    """ 

    :type: str
    """

    float: float
    """ 

    :type: float
    """

    float_array: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    group: PropertyGroup
    """ 

    :type: PropertyGroup
    """

    id: ID
    """ 

    :type: ID
    """

    idp_array: bpy_prop_collection[PropertyGroup]
    """ 

    :type: bpy_prop_collection[PropertyGroup]
    """

    int: int
    """ 

    :type: int
    """

    int_array: bpy_prop_array[int]
    """ 

    :type: bpy_prop_array[int]
    """

    string: str
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
