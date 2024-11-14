import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .image import Image

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataImages(bpy_prop_collection[Image], bpy_struct):
    """Collection of images"""

    def new(
        self,
        name: str | typing.Any,
        width: int | None,
        height: int | None,
        alpha: bool | typing.Any | None = False,
        float_buffer: bool | typing.Any | None = False,
        stereo3d: bool | typing.Any | None = False,
        is_data: bool | typing.Any | None = False,
        tiled: bool | typing.Any | None = False,
    ) -> Image:
        """Add a new image to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param width: Width of the image
        :type width: int | None
        :param height: Height of the image
        :type height: int | None
        :param alpha: Alpha, Use alpha channel
        :type alpha: bool | typing.Any | None
        :param float_buffer: Float Buffer, Create an image with floating-point color
        :type float_buffer: bool | typing.Any | None
        :param stereo3d: Stereo 3D, Create left and right views
        :type stereo3d: bool | typing.Any | None
        :param is_data: Is Data, Create image with non-color data color space
        :type is_data: bool | typing.Any | None
        :param tiled: Tiled, Create a tiled image
        :type tiled: bool | typing.Any | None
        :return: New image data-block
        :rtype: Image
        """
        ...

    def load(
        self,
        filepath: str | typing.Any,
        check_existing: bool | typing.Any | None = False,
    ) -> Image:
        """Load a new image into the main database

        :param filepath: Path of the file to load
        :type filepath: str | typing.Any
        :param check_existing: Using existing data-block if this file is already loaded
        :type check_existing: bool | typing.Any | None
        :return: New image data-block
        :rtype: Image
        """
        ...

    def remove(
        self,
        image: Image,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove an image from the current blendfile

        :param image: Image to remove
        :type image: Image
        :param do_unlink: Unlink all usages of this image before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this image
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this image
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
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
