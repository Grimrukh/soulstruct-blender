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


class ThemeSequenceEditor(bpy_struct):
    """Theme settings for the Sequence Editor"""

    active_strip: mathutils.Color | None
    """ 

    :type: mathutils.Color | None
    """

    audio_strip: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    color_strip: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    draw_action: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    effect_strip: mathutils.Color
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

    image_strip: mathutils.Color
    """ 

    :type: mathutils.Color
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

    keyframe_movehold: mathutils.Color
    """ Color of moving hold keyframe

    :type: mathutils.Color
    """

    keyframe_movehold_selected: mathutils.Color
    """ Color of selected moving hold keyframe

    :type: mathutils.Color
    """

    keyframe_selected: mathutils.Color
    """ Color of selected keyframe

    :type: mathutils.Color
    """

    mask_strip: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    meta_strip: mathutils.Color
    """ 

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

    movie_strip: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    movieclip_strip: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    preview_back: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    preview_range: bpy_prop_array[float]
    """ Color of preview range overlay

    :type: bpy_prop_array[float]
    """

    row_alternate: bpy_prop_array[float]
    """ Overlay color on every other row

    :type: bpy_prop_array[float]
    """

    scene_strip: mathutils.Color
    """ 

    :type: mathutils.Color
    """

    selected_strip: mathutils.Color
    """ 

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

    text_strip: mathutils.Color
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

    transition_strip: mathutils.Color
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
