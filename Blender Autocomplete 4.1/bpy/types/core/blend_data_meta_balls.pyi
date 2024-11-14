import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .meta_ball import MetaBall
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataMetaBalls(bpy_prop_collection[MetaBall], bpy_struct):
    """Collection of metaballs"""

    def new(self, name: str | typing.Any) -> MetaBall:
        """Add a new metaball to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New metaball data-block
        :rtype: MetaBall
        """
        ...

    def remove(
        self,
        metaball: MetaBall,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a metaball from the current blendfile

        :param metaball: Metaball to remove
        :type metaball: MetaBall
        :param do_unlink: Unlink all usages of this metaball before deleting it (WARNING: will also delete objects instancing that metaball data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this metaball data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this metaball data
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
