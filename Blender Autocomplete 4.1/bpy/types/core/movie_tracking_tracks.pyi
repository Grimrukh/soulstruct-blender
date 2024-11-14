import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_track import MovieTrackingTrack

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingTracks(bpy_prop_collection[MovieTrackingTrack], bpy_struct):
    """Collection of movie tracking tracks"""

    active: MovieTrackingTrack | None
    """ Active track in this tracking data object. Deprecated, use objects[name].tracks.active

    :type: MovieTrackingTrack | None
    """

    def new(
        self, name: str | typing.Any = "", frame: typing.Any | None = 1
    ) -> MovieTrackingTrack:
        """Create new motion track in this movie clip

        :param name: Name of new track
        :type name: str | typing.Any
        :param frame: Frame, Frame number to add track on
        :type frame: typing.Any | None
        :return: Newly created track
        :rtype: MovieTrackingTrack
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
