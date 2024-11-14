import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_reconstruction import MovieTrackingReconstruction
from .movie_tracking_object_tracks import MovieTrackingObjectTracks
from .movie_tracking_object_plane_tracks import MovieTrackingObjectPlaneTracks

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingObject(bpy_struct):
    """Match-moving object tracking and reconstruction data"""

    is_camera: bool
    """ Object is used for camera tracking

    :type: bool
    """

    keyframe_a: int
    """ First keyframe used for reconstruction initialization

    :type: int
    """

    keyframe_b: int
    """ Second keyframe used for reconstruction initialization

    :type: int
    """

    name: str
    """ Unique name of object

    :type: str
    """

    plane_tracks: MovieTrackingObjectPlaneTracks
    """ Collection of plane tracks in this tracking data object

    :type: MovieTrackingObjectPlaneTracks
    """

    reconstruction: MovieTrackingReconstruction
    """ 

    :type: MovieTrackingReconstruction
    """

    scale: float
    """ Scale of object solution in camera space

    :type: float
    """

    tracks: MovieTrackingObjectTracks
    """ Collection of tracks in this tracking data object

    :type: MovieTrackingObjectTracks
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
