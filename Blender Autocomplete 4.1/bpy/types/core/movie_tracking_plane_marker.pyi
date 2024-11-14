import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingPlaneMarker(bpy_struct):
    """Match-moving plane marker data for tracking"""

    corners: list[list[float]] | tuple[
        tuple[float, float, float, float], tuple[float, float, float, float]
    ]
    """ Array of coordinates which represents UI rectangle corners in frame normalized coordinates

    :type: list[list[float]] | tuple[tuple[float, float, float, float], tuple[float, float, float, float]]
    """

    frame: int
    """ Frame number marker is keyframed on

    :type: int
    """

    mute: bool
    """ Is marker muted for current frame

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
