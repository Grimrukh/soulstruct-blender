import typing
import collections.abc
import mathutils
from .struct import Struct
from .theme_space_list_generic import ThemeSpaceListGeneric
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .theme_space_generic import ThemeSpaceGeneric

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ThemeGraphEditor(bpy_struct):
    """Theme settings for the graph editor"""

    active_channels_group: mathutils.Color | None
    """ 

    :type: mathutils.Color | None
    """

    channel_group: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    channels_region: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    dopesheet_channel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    dopesheet_subchannel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    frame_current: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    grid: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_align: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_auto: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_auto_clamped: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_free: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_align: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_auto: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_auto_clamped: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_free: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_sel_vect: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vect: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vertex: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vertex_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    handle_vertex_size: int
    """ 

    :type: int
    """

    lastsel_point: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    preview_range: bpy_prop_array[float]
    """ Color of preview range overlay

    :type: bpy_prop_array[float]
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
    """

    space_list: ThemeSpaceListGeneric
    """ Settings for space list

    :type: ThemeSpaceListGeneric
    """

    time_marker_line: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    time_marker_line_selected: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    time_scrub_background: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    vertex: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_active: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_bevel: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_select: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    vertex_size: int
    """ 

    :type: int
    """

    vertex_unreferenced: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    window_sliders: mathutils.Color
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
