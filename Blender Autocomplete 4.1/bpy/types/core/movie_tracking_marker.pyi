import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingMarker(bpy_struct):
    """Match-moving marker data for tracking"""

    co: mathutils.Vector
    """ Marker position at frame in normalized coordinates

    :type: mathutils.Vector
    """

    frame: int
    """ Frame number marker is keyframed on

    :type: int
    """

    is_keyed: bool
    """ Whether the position of the marker is keyframed or tracked

    :type: bool
    """

    mute: bool
    """ Is marker muted for current frame

    :type: bool
    """

    pattern_bound_box: list[list[float]] | tuple[
        tuple[float, float], tuple[float, float]
    ]
    """ Pattern area bounding box in normalized coordinates

    :type: list[list[float]] | tuple[tuple[float, float], tuple[float, float]]
    """

    pattern_corners: list[list[float]] | tuple[
        tuple[float, float, float, float], tuple[float, float, float, float]
    ]
    """ Array of coordinates which represents pattern's corners in normalized coordinates relative to marker position

    :type: list[list[float]] | tuple[tuple[float, float, float, float], tuple[float, float, float, float]]
    """

    search_max: mathutils.Vector
    """ Right-bottom corner of search area in normalized coordinates relative to marker position

    :type: mathutils.Vector
    """

    search_min: mathutils.Vector
    """ Left-bottom corner of search area in normalized coordinates relative to marker position

    :type: mathutils.Vector
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
