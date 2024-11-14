import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .movie_tracking_plane_marker import MovieTrackingPlaneMarker
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingPlaneMarkers(
    bpy_prop_collection[MovieTrackingPlaneMarker], bpy_struct
):
    """Collection of markers for movie tracking plane track"""

    def find_frame(
        self, frame: int | None, exact: bool | typing.Any | None = True
    ) -> MovieTrackingPlaneMarker:
        """Get plane marker for specified frame

        :param frame: Frame, Frame number to find marker for
        :type frame: int | None
        :param exact: Exact, Get plane marker at exact frame number rather than get estimated marker
        :type exact: bool | typing.Any | None
        :return: Plane marker for specified frame
        :rtype: MovieTrackingPlaneMarker
        """
        ...

    def insert_frame(self, frame: int | None) -> MovieTrackingPlaneMarker:
        """Insert a new plane marker at the specified frame

        :param frame: Frame, Frame number to insert marker to
        :type frame: int | None
        :return: Newly created plane marker
        :rtype: MovieTrackingPlaneMarker
        """
        ...

    def delete_frame(self, frame: int | None):
        """Delete plane marker at specified frame

        :param frame: Frame, Frame number to delete plane marker from
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
