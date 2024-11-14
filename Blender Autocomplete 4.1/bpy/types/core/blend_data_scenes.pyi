import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataScenes(bpy_prop_collection[Scene], bpy_struct):
    """Collection of scenes"""

    def new(self, name: str | typing.Any) -> Scene:
        """Add a new scene to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New scene data-block
        :rtype: Scene
        """
        ...

    def remove(self, scene: Scene, do_unlink: bool | typing.Any | None = True):
        """Remove a scene from the current blendfile

        :param scene: Scene to remove
        :type scene: Scene
        :param do_unlink: Unlink all usages of this scene before deleting it
        :type do_unlink: bool | typing.Any | None
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
