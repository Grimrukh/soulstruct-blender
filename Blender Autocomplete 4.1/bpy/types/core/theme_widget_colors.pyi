import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeWidgetColors(bpy_struct):
    """Theme settings for widget color sets"""

    inner: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    inner_sel: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    item: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    outline: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    roundness: float
    """ Amount of edge rounding

    :type: float
    """

    shadedown: int
    """ 

    :type: int
    """

    shadetop: int
    """ 

    :type: int
    """

    show_shaded: bool
    """ 

    :type: bool
    """

    text: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    text_sel: mathutils.Color
    """ 

    :type: mathutils.Color
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
