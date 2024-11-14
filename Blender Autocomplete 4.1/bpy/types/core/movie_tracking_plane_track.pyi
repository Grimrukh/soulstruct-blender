import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .image import Image
from .movie_tracking_plane_markers import MovieTrackingPlaneMarkers

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingPlaneTrack(bpy_struct):
    """Match-moving plane track data for tracking"""

    image: Image
    """ Image displayed in the track during editing in clip editor

    :type: Image
    """

    image_opacity: float
    """ Opacity of the image

    :type: float
    """

    markers: MovieTrackingPlaneMarkers
    """ Collection of markers in track

    :type: MovieTrackingPlaneMarkers
    """

    name: str
    """ Unique name of track

    :type: str
    """

    select: bool
    """ Plane track is selected

    :type: bool
    """

    use_auto_keying: bool
    """ Automatic keyframe insertion when moving plane corners

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
