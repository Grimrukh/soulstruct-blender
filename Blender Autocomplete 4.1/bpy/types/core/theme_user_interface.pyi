import typing
import collections.abc
import mathutils
from .theme_widget_state_colors import ThemeWidgetStateColors
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_widget_colors import ThemeWidgetColors

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeUserInterface(bpy_struct):
    """Theme settings for user interface elements"""

    axis_x: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    axis_y: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    axis_z: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    editor_outline: mathutils.Color
    """ Color of the outline of the editors and their round corners

    :type: mathutils.Color
    """

    gizmo_a: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gizmo_b: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gizmo_hi: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gizmo_primary: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gizmo_secondary: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    gizmo_view_align: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    icon_alpha: float
    """ Transparency of icons in the interface, to reduce contrast

    :type: float
    """

    icon_border_intensity: float
    """ Control the intensity of the border around themes icons

    :type: float
    """

    icon_collection: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    icon_folder: bpy_prop_array[float]
    """ Color of folders in the file browser

    :type: bpy_prop_array[float]
    """

    icon_modifier: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    icon_object: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    icon_object_data: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    icon_saturation: float
    """ Saturation of icons in the interface

    :type: float
    """

    icon_scene: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    icon_shading: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    menu_shadow_fac: float
    """ Blending factor for menu shadows

    :type: float
    """

    menu_shadow_width: int
    """ Width of menu shadows, set to zero to disable

    :type: int
    """

    panel_roundness: float
    """ Roundness of the corners of panels and sub-panels

    :type: float
    """

    transparent_checker_primary: mathutils.Color
    """ Primary color of checkerboard pattern indicating transparent areas

    :type: mathutils.Color
    """

    transparent_checker_secondary: mathutils.Color
    """ Secondary color of checkerboard pattern indicating transparent areas

    :type: mathutils.Color
    """

    transparent_checker_size: int
    """ Size of checkerboard pattern indicating transparent areas

    :type: int
    """

    wcol_box: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_list_item: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_menu: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_menu_back: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_menu_item: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_num: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_numslider: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_option: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_pie_menu: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_progress: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_pulldown: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_radio: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_regular: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_scroll: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_state: ThemeWidgetStateColors
    """ 

    :type: ThemeWidgetStateColors
    """

    wcol_tab: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_text: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_toggle: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_tool: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_toolbar_item: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    wcol_tooltip: ThemeWidgetColors
    """ 

    :type: ThemeWidgetColors
    """

    widget_emboss: bpy_prop_array[float]
    """ Color of the 1px shadow line underlying widgets

    :type: bpy_prop_array[float]
    """

    widget_text_cursor: mathutils.Color
    """ Color of the text insertion cursor (caret)

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
