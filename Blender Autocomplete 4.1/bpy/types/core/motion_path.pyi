import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .motion_path_vert import MotionPathVert

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MotionPath(bpy_struct):
    """Cache of the world-space positions of an element over a frame range"""

    color: mathutils.Color
    """ Custom color for motion path

    :type: mathutils.Color
    """

    frame_end: int
    """ End frame of the stored range

    :type: int
    """

    frame_start: int
    """ Starting frame of the stored range

    :type: int
    """

    is_modified: bool
    """ Path is being edited

    :type: bool
    """

    length: int
    """ Number of frames cached

    :type: int
    """

    line_thickness: int
    """ Line thickness for motion path

    :type: int
    """

    lines: bool
    """ Use straight lines between keyframe points

    :type: bool
    """

    points: bpy_prop_collection[MotionPathVert]
    """ Cached positions per frame

    :type: bpy_prop_collection[MotionPathVert]
    """

    use_bone_head: bool
    """ For PoseBone paths, use the bone head location when calculating this path

    :type: bool
    """

    use_custom_color: bool
    """ Use custom color for this motion path

    :type: bool
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
