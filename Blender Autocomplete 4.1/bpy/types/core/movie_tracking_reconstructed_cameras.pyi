import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .movie_reconstructed_camera import MovieReconstructedCamera
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingReconstructedCameras(
    bpy_prop_collection[MovieReconstructedCamera], bpy_struct
):
    """Collection of solved cameras"""

    def find_frame(self, frame: typing.Any | None = 1) -> MovieReconstructedCamera:
        """Find a reconstructed camera for a give frame number

        :param frame: Frame, Frame number to find camera for
        :type frame: typing.Any | None
        :return: Camera for a given frame
        :rtype: MovieReconstructedCamera
        """
        ...

    def matrix_from_frame(self, frame: typing.Any | None = 1) -> mathutils.Matrix:
        """Return interpolated camera matrix for a given frame

        :param frame: Frame, Frame number to find camera for
        :type frame: typing.Any | None
        :return: Matrix, Interpolated camera matrix for a given frame
        :rtype: mathutils.Matrix
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
