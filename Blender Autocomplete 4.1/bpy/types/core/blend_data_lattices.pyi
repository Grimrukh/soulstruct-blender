import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .lattice import Lattice

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataLattices(bpy_prop_collection[Lattice], bpy_struct):
    """Collection of lattices"""

    def new(self, name: str | typing.Any) -> Lattice:
        """Add a new lattice to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New lattice data-block
        :rtype: Lattice
        """
        ...

    def remove(
        self,
        lattice: Lattice,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a lattice from the current blendfile

        :param lattice: Lattice to remove
        :type lattice: Lattice
        :param do_unlink: Unlink all usages of this lattice before deleting it (WARNING: will also delete objects instancing that lattice data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this lattice data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this lattice data
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
