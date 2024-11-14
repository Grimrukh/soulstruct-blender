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


class ThemeNLAEditor(bpy_struct):
    """Theme settings for the NLA Editor"""

    active_action: bpy_prop_array[float] | None
    """ Animation data-block has active action

    :type: bpy_prop_array[float] | None
    """

    active_action_unset: bpy_prop_array[float] | None
    """ Animation data-block doesn't have active action

    :type: bpy_prop_array[float] | None
    """

    dopesheet_channel: mathutils.Color
    """ Nonlinear Animation Channel

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

    keyframe_border: bpy_prop_array[float]
    """ Color of keyframe border

    :type: bpy_prop_array[float]
    """

    keyframe_border_selected: bpy_prop_array[float]
    """ Color of selected keyframe border

    :type: bpy_prop_array[float]
    """

    meta_strips: mathutils.Color
    """ Unselected Meta Strip (for grouping related strips)

    :type: mathutils.Color
    """

    meta_strips_selected: mathutils.Color
    """ Selected Meta Strip (for grouping related strips)

    :type: mathutils.Color
    """

    nla_track: mathutils.Color
    """ Nonlinear Animation Track

    :type: mathutils.Color
    """

    preview_range: bpy_prop_array[float]
    """ Color of preview range overlay

    :type: bpy_prop_array[float]
    """

    sound_strips: mathutils.Color
    """ Unselected Sound Strip (for timing speaker sounds)

    :type: mathutils.Color
    """

    sound_strips_selected: mathutils.Color
    """ Selected Sound Strip (for timing speaker sounds)

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
    """ Unselected Action-Clip Strip

    :type: mathutils.Color
    """

    strips_selected: mathutils.Color
    """ Selected Action-Clip Strip

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

    transition_strips: mathutils.Color
    """ Unselected Transition Strip

    :type: mathutils.Color
    """

    transition_strips_selected: mathutils.Color
    """ Selected Transition Strip

    :type: mathutils.Color
    """

    tweak: mathutils.Color
    """ Color for strip/action being "tweaked" or edited

    :type: mathutils.Color
    """

    tweak_duplicate: mathutils.Color
    """ Warning/error indicator color for strips referencing the strip being tweaked

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
