import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .movie_tracking_reconstructed_cameras import MovieTrackingReconstructedCameras

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingReconstruction(bpy_struct):
    """Match-moving reconstruction data from tracker"""

    average_error: float
    """ Average error of reconstruction

    :type: float
    """

    cameras: MovieTrackingReconstructedCameras
    """ Collection of solved cameras

    :type: MovieTrackingReconstructedCameras
    """

    is_valid: bool
    """ Is tracking data contains valid reconstruction information

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
