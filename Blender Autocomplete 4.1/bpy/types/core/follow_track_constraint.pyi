import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object
from .movie_clip import MovieClip

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FollowTrackConstraint(Constraint, bpy_struct):
    """Lock motion to the target motion track"""

    camera: Object
    """ Camera to which motion is parented (if empty active scene camera is used)

    :type: Object
    """

    clip: MovieClip
    """ Movie Clip to get tracking data from

    :type: MovieClip
    """

    depth_object: Object
    """ Object used to define depth in camera space by projecting onto surface of this object

    :type: Object
    """

    frame_method: str
    """ How the footage fits in the camera frame

    :type: str
    """

    object: str
    """ Movie tracking object to follow (if empty, camera object is used)

    :type: str
    """

    track: str
    """ Movie tracking track to follow

    :type: str
    """

    use_3d_position: bool
    """ Use 3D position of track to parent to

    :type: bool
    """

    use_active_clip: bool
    """ Use active clip defined in scene

    :type: bool
    """

    use_undistorted_position: bool
    """ Parent to undistorted position of 2D track

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
