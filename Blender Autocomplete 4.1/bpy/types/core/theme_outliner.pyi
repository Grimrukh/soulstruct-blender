import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeOutliner(bpy_struct):
    """Theme settings for the Outliner"""

    active: mathutils.Color | None
    """ 

    :type: mathutils.Color | None
    """

    active_object: mathutils.Color | None
    """ 

    :type: mathutils.Color | None
    """

    edited_object: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    match: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    row_alternate: bpy_prop_array[float]
    """ Overlay color on every other row

    :type: bpy_prop_array[float]
    """

    selected_highlight: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    selected_object: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
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
