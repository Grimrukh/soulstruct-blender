import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeInfo(bpy_struct):
    """Theme settings for Info"""

    info_debug: bpy_prop_array[float]
    """ Background color of Debug icon

    :type: bpy_prop_array[float]
    """

    info_debug_text: mathutils.Color
    """ Foreground color of Debug icon

    :type: mathutils.Color
    """

    info_error: bpy_prop_array[float]
    """ Background color of Error icon

    :type: bpy_prop_array[float]
    """

    info_error_text: mathutils.Color
    """ Foreground color of Error icon

    :type: mathutils.Color
    """

    info_info: bpy_prop_array[float]
    """ Background color of Info icon

    :type: bpy_prop_array[float]
    """

    info_info_text: mathutils.Color
    """ Foreground color of Info icon

    :type: mathutils.Color
    """

    info_operator: bpy_prop_array[float]
    """ Background color of Operator icon

    :type: bpy_prop_array[float]
    """

    info_operator_text: mathutils.Color
    """ Foreground color of Operator icon

    :type: mathutils.Color
    """

    info_property: bpy_prop_array[float]
    """ Background color of Property icon

    :type: bpy_prop_array[float]
    """

    info_property_text: mathutils.Color
    """ Foreground color of Property icon

    :type: mathutils.Color
    """

    info_selected: mathutils.Color
    """ Background color of selected line

    :type: mathutils.Color
    """

    info_selected_text: mathutils.Color
    """ Text color of selected line

    :type: mathutils.Color
    """

    info_warning: bpy_prop_array[float]
    """ Background color of Warning icon

    :type: bpy_prop_array[float]
    """

    info_warning_text: mathutils.Color
    """ Foreground color of Warning icon

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
