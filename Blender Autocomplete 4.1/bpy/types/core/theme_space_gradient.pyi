import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .theme_gradient_colors import ThemeGradientColors
from .bpy_prop_array import bpy_prop_array
from .theme_panel_colors import ThemePanelColors

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeSpaceGradient(bpy_struct):
    button: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    button_text: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    button_text_hi: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    button_title: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    execution_buts: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    gradients: ThemeGradientColors
    """ 

    :type: ThemeGradientColors
    """

    header: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    header_text: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    header_text_hi: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    navigation_bar: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    panelcolors: ThemePanelColors
    """ 

    :type: ThemePanelColors
    """

    tab_active: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    tab_back: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    tab_inactive: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    tab_outline: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    text: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    text_hi: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    title: mathutils.Color
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
