import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .curves import Curves

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataHairCurves(bpy_prop_collection[Curves], bpy_struct):
    """Collection of hair curves"""

    def new(self, name: str | typing.Any) -> Curves:
        """Add a new hair to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New curves data-block
        :rtype: Curves
        """
        ...

    def remove(
        self,
        curves: Curves,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a curves data-block from the current blendfile

        :param curves: Curves data-block to remove
        :type curves: Curves
        :param do_unlink: Unlink all usages of this curves before deleting it (WARNING: will also delete objects instancing that curves data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this curves data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this curves data
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
