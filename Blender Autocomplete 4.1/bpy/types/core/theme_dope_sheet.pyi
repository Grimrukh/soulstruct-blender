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


class ThemeDopeSheet(bpy_struct):
    """Theme settings for the Dope Sheet"""

    active_channels_group: bpy_prop_array[float] | None
    """ 

    :type: bpy_prop_array[float] | None
    """

    channel_group: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    channels: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    channels_selected: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    dopesheet_channel: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    dopesheet_subchannel: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    frame_current: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    grid: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    interpolation_line: bpy_prop_array[float]
    """ Color of lines showing non-Bézier interpolation modes

    :type: bpy_prop_array[float]
    """

    keyframe: mathutils.Color
    """ Color of Keyframe

    :type: mathutils.Color
    """

    keyframe_border: bpy_prop_array[float]
    """ Color of keyframe border

    :type: bpy_prop_array[float]
    """

    keyframe_border_selected: bpy_prop_array[float]
    """ Color of selected keyframe border

    :type: bpy_prop_array[float]
    """

    keyframe_breakdown: mathutils.Color
    """ Color of breakdown keyframe

    :type: mathutils.Color
    """

    keyframe_breakdown_selected: mathutils.Color
    """ Color of selected breakdown keyframe

    :type: mathutils.Color
    """

    keyframe_extreme: mathutils.Color
    """ Color of extreme keyframe

    :type: mathutils.Color
    """

    keyframe_extreme_selected: mathutils.Color
    """ Color of selected extreme keyframe

    :type: mathutils.Color
    """

    keyframe_jitter: mathutils.Color
    """ Color of jitter keyframe

    :type: mathutils.Color
    """

    keyframe_jitter_selected: mathutils.Color
    """ Color of selected jitter keyframe

    :type: mathutils.Color
    """

    keyframe_movehold: mathutils.Color
    """ Color of moving hold keyframe

    :type: mathutils.Color
    """

    keyframe_movehold_selected: mathutils.Color
    """ Color of selected moving hold keyframe

    :type: mathutils.Color
    """

    keyframe_scale_factor: float
    """ Scale factor for adjusting the height of keyframes

    :type: float
    """

    keyframe_selected: mathutils.Color
    """ Color of selected keyframe

    :type: mathutils.Color
    """

    long_key: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    long_key_selected: bpy_prop_array[float]
    """ 

    :type: bpy_prop_array[float]
    """

    preview_range: bpy_prop_array[float]
    """ Color of preview range overlay

    :type: bpy_prop_array[float]
    """

    simulated_frames: bpy_prop_array[float]
    """ 

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

    summary: bpy_prop_array[float]
    """ Color of summary channel

    :type: bpy_prop_array[float]
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

    value_sliders: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    view_sliders: mathutils.Color
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
