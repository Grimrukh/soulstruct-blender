import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .mask import Mask
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataMasks(bpy_prop_collection[Mask], bpy_struct):
    """Collection of masks"""

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    def new(self, name: str | typing.Any) -> Mask:
        """Add a new mask with a given name to the main database

        :param name: Mask, Name of new mask data-block
        :type name: str | typing.Any
        :return: New mask data-block
        :rtype: Mask
        """
        ...

    def remove(
        self,
        mask: Mask,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a mask from the current blendfile

        :param mask: Mask to remove
        :type mask: Mask
        :param do_unlink: Unlink all usages of this mask before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this mask
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this mask
        :type do_ui_user: bool | typing.Any | None
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
