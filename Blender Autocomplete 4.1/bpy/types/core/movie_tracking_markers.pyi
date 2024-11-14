import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .movie_tracking_marker import MovieTrackingMarker
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingMarkers(bpy_prop_collection[MovieTrackingMarker], bpy_struct):
    """Collection of markers for movie tracking track"""

    def find_frame(
        self, frame: int | None, exact: bool | typing.Any | None = True
    ) -> MovieTrackingMarker:
        """Get marker for specified frame

        :param frame: Frame, Frame number to find marker for
        :type frame: int | None
        :param exact: Exact, Get marker at exact frame number rather than get estimated marker
        :type exact: bool | typing.Any | None
        :return: Marker for specified frame
        :rtype: MovieTrackingMarker
        """
        ...

    def insert_frame(
        self, frame: int | None, co: typing.Any | None = (0.0, 0.0)
    ) -> MovieTrackingMarker:
        """Insert a new marker at the specified frame

        :param frame: Frame, Frame number to insert marker to
        :type frame: int | None
        :param co: Coordinate, Place new marker at the given frame using specified in normalized space coordinates
        :type co: typing.Any | None
        :return: Newly created marker
        :rtype: MovieTrackingMarker
        """
        ...

    def delete_frame(self, frame: int | None):
        """Delete marker at specified frame

        :param frame: Frame, Frame number to delete marker from
        :type frame: int | None
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
