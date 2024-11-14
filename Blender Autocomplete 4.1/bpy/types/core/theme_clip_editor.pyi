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


class ThemeClipEditor(bpy_struct):
    """Theme settings for the Movie Clip Editor"""

    active_marker: mathutils.Color | None
    """ Color of active marker

    :type: mathutils.Color | None
    """

    disabled_marker: mathutils.Color
    """ Color of disabled marker

    :type: mathutils.Color
    """

    frame_current: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    grid: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
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

    locked_marker: mathutils.Color
    """ Color of locked marker

    :type: mathutils.Color
    """

    marker: mathutils.Color
    """ Color of marker

    :type: mathutils.Color
    """

    marker_outline: mathutils.Color
    """ Color of marker's outline

    :type: mathutils.Color
    """

    metadatabg: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    metadatatext: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    path_after: mathutils.Color
    """ Color of path after current frame

    :type: mathutils.Color
    """

    path_before: mathutils.Color
    """ Color of path before current frame

    :type: mathutils.Color
    """

    path_keyframe_after: mathutils.Color
    """ Color of path after current frame

    :type: mathutils.Color
    """

    path_keyframe_before: mathutils.Color
    """ Color of path before current frame

    :type: mathutils.Color
    """

    selected_marker: mathutils.Color
    """ Color of selected marker

    :type: mathutils.Color
    """

    space: ThemeSpaceGeneric
    """ Settings for space

    :type: ThemeSpaceGeneric
    """

    space_list: ThemeSpaceListGeneric
    """ Settings for space list

    :type: ThemeSpaceListGeneric
    """

    strips: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    strips_selected: mathutils.Color
    """ 

    :type: mathutils.Color
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
