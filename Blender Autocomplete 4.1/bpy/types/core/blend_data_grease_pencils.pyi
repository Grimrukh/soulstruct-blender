import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .grease_pencil import GreasePencil

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataGreasePencils(bpy_prop_collection[GreasePencil], bpy_struct):
    """Collection of grease pencils"""

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    def new(self, name: str | typing.Any) -> GreasePencil:
        """Add a new grease pencil datablock to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New grease pencil data-block
        :rtype: GreasePencil
        """
        ...

    def remove(
        self,
        grease_pencil: GreasePencil,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a grease pencil instance from the current blendfile

        :param grease_pencil: Grease Pencil to remove
        :type grease_pencil: GreasePencil
        :param do_unlink: Unlink all usages of this grease pencil before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this grease pencil
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this grease pencil
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
