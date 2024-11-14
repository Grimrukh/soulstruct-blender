import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .id import ID
from .area import Area

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Screen(ID, bpy_struct):
    """Screen data-block, defining the layout of areas in a window"""

    areas: bpy_prop_collection[Area]
    """ Areas the screen is subdivided into

    :type: bpy_prop_collection[Area]
    """

    is_animation_playing: bool
    """ Animation playback is active

    :type: bool
    """

    is_scrubbing: bool
    """ True when the user is scrubbing through time

    :type: bool
    """

    is_temporary: bool
    """ 

    :type: bool
    """

    show_fullscreen: bool
    """ An area is maximized, filling this screen

    :type: bool
    """

    show_statusbar: bool
    """ Show status bar

    :type: bool
    """

    use_follow: bool
    """ Follow current frame in editors

    :type: bool
    """

    use_play_3d_editors: bool
    """ 

    :type: bool
    """

    use_play_animation_editors: bool
    """ 

    :type: bool
    """

    use_play_clip_editors: bool
    """ 

    :type: bool
    """

    use_play_image_editors: bool
    """ 

    :type: bool
    """

    use_play_node_editors: bool
    """ 

    :type: bool
    """

    use_play_properties_editors: bool
    """ 

    :type: bool
    """

    use_play_sequence_editors: bool
    """ 

    :type: bool
    """

    use_play_spreadsheet_editors: bool
    """ 

    :type: bool
    """

    use_play_top_left_3d_editor: bool
    """ 

    :type: bool
    """

    def statusbar_info(self) -> str | typing.Any:
        """statusbar_info

        :return: Status Bar Info
        :rtype: str | typing.Any
        """
        ...

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
