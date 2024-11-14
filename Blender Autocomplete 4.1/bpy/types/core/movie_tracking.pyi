import typing
import collections.abc
import mathutils
from .movie_tracking_plane_tracks import MovieTrackingPlaneTracks
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_objects import MovieTrackingObjects
from .movie_tracking_reconstruction import MovieTrackingReconstruction
from .movie_tracking_dopesheet import MovieTrackingDopesheet
from .movie_tracking_tracks import MovieTrackingTracks
from .movie_tracking_stabilization import MovieTrackingStabilization
from .movie_tracking_camera import MovieTrackingCamera
from .movie_tracking_settings import MovieTrackingSettings

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTracking(bpy_struct):
    """Match-moving data for tracking"""

    active_object_index: int | None
    """ Index of active object

    :type: int | None
    """

    camera: MovieTrackingCamera
    """ 

    :type: MovieTrackingCamera
    """

    dopesheet: MovieTrackingDopesheet
    """ 

    :type: MovieTrackingDopesheet
    """

    objects: MovieTrackingObjects
    """ Collection of objects in this tracking data object

    :type: MovieTrackingObjects
    """

    plane_tracks: MovieTrackingPlaneTracks
    """ Collection of plane tracks in this tracking data object. Deprecated, use objects[name].plane_tracks

    :type: MovieTrackingPlaneTracks
    """

    reconstruction: MovieTrackingReconstruction
    """ 

    :type: MovieTrackingReconstruction
    """

    settings: MovieTrackingSettings
    """ 

    :type: MovieTrackingSettings
    """

    stabilization: MovieTrackingStabilization
    """ 

    :type: MovieTrackingStabilization
    """

    tracks: MovieTrackingTracks
    """ Collection of tracks in this tracking data object. Deprecated, use objects[name].tracks

    :type: MovieTrackingTracks
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
