import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .camera import Camera
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataCameras(bpy_prop_collection[Camera], bpy_struct):
    """Collection of cameras"""

    def new(self, name: str | typing.Any) -> Camera:
        """Add a new camera to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New camera data-block
        :rtype: Camera
        """
        ...

    def remove(
        self,
        camera: Camera,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a camera from the current blendfile

        :param camera: Camera to remove
        :type camera: Camera
        :param do_unlink: Unlink all usages of this camera before deleting it (WARNING: will also delete objects instancing that camera data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this camera
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this camera
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
