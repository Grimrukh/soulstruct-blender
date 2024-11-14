import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .texture import Texture

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataTextures(bpy_prop_collection[Texture], bpy_struct):
    """Collection of textures"""

    def new(self, name: str | typing.Any, type: str | None) -> Texture:
        """Add a new texture to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param type: Type, The type of texture to add
        :type type: str | None
        :return: New texture data-block
        :rtype: Texture
        """
        ...

    def remove(
        self,
        texture: Texture,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a texture from the current blendfile

        :param texture: Texture to remove
        :type texture: Texture
        :param do_unlink: Unlink all usages of this texture before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this texture
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this texture
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
