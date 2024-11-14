import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_plane_track import MovieTrackingPlaneTrack
from .movie_tracking_track import MovieTrackingTrack

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingObjectPlaneTracks(
    bpy_prop_collection[MovieTrackingPlaneTrack], bpy_struct
):
    """Collection of tracking plane tracks"""

    active: MovieTrackingTrack | None
    """ Active track in this tracking data object

    :type: MovieTrackingTrack | None
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
