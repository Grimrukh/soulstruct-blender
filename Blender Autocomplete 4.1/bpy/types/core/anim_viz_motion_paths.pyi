import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class AnimVizMotionPaths(bpy_struct):
    """Motion Path settings for animation visualization"""

    bake_in_camera_space: bool
    """ Motion path points will be baked into the camera space of the active camera. This means they will only look right when looking through that camera. Switching cameras using markers is not supported

    :type: bool
    """

    bake_location: str
    """ When calculating Bone Paths, use Head or Tips

    :type: str
    """

    frame_after: int
    """ Number of frames to show after the current frame (only for 'Around Current Frame' Onion-skinning method)

    :type: int
    """

    frame_before: int
    """ Number of frames to show before the current frame (only for 'Around Current Frame' Onion-skinning method)

    :type: int
    """

    frame_end: int
    """ End frame of range of paths to display/calculate (not for 'Around Current Frame' Onion-skinning method)

    :type: int
    """

    frame_start: int
    """ Starting frame of range of paths to display/calculate (not for 'Around Current Frame' Onion-skinning method)

    :type: int
    """

    frame_step: int
    """ Number of frames between paths shown (not for 'On Keyframes' Onion-skinning method)

    :type: int
    """

    has_motion_paths: bool
    """ Are there any bone paths that will need updating (read-only)

    :type: bool
    """

    range: str
    """ Type of range to calculate for Motion Paths

    :type: str
    """

    show_frame_numbers: bool
    """ Show frame numbers on Motion Paths

    :type: bool
    """

    show_keyframe_action_all: bool
    """ For bone motion paths, search whole Action for keyframes instead of in group with matching name only (is slower)

    :type: bool
    """

    show_keyframe_highlight: bool
    """ Emphasize position of keyframes on Motion Paths

    :type: bool
    """

    show_keyframe_numbers: bool
    """ Show frame numbers of Keyframes on Motion Paths

    :type: bool
    """

    type: str
    """ Type of range to show for Motion Paths

    :type: str
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
