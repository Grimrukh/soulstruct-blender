import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_plane_track import MovieTrackingPlaneTrack

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingPlaneTracks(
    bpy_prop_collection[MovieTrackingPlaneTrack], bpy_struct
):
    """Collection of movie tracking plane tracks"""

    active: MovieTrackingPlaneTrack | None
    """ Active plane track in this tracking data object. Deprecated, use objects[name].plane_tracks.active

    :type: MovieTrackingPlaneTrack | None
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
