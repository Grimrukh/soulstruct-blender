import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .camera_background_image import CameraBackgroundImage

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class CameraBackgroundImages(bpy_prop_collection[CameraBackgroundImage], bpy_struct):
    """Collection of background images"""

    def new(self) -> CameraBackgroundImage:
        """Add new background image

        :return: Image displayed as viewport background
        :rtype: CameraBackgroundImage
        """
        ...

    def remove(self, image: CameraBackgroundImage):
        """Remove background image

        :param image: Image displayed as viewport background
        :type image: CameraBackgroundImage
        """
        ...

    def clear(self):
        """Remove all background images"""
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
