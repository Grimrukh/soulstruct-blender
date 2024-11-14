import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .armature import Armature

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataArmatures(bpy_prop_collection[Armature], bpy_struct):
    """Collection of armatures"""

    def new(self, name: str | typing.Any) -> Armature:
        """Add a new armature to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New armature data-block
        :rtype: Armature
        """
        ...

    def remove(
        self,
        armature: Armature,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove an armature from the current blendfile

        :param armature: Armature to remove
        :type armature: Armature
        :param do_unlink: Unlink all usages of this armature before deleting it (WARNING: will also delete objects instancing that armature data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this armature data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this armature data
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
