import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .speaker import Speaker
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataSpeakers(bpy_prop_collection[Speaker], bpy_struct):
    """Collection of speakers"""

    def new(self, name: str | typing.Any) -> Speaker:
        """Add a new speaker to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New speaker data-block
        :rtype: Speaker
        """
        ...

    def remove(
        self,
        speaker: Speaker,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a speaker from the current blendfile

        :param speaker: Speaker to remove
        :type speaker: Speaker
        :param do_unlink: Unlink all usages of this speaker before deleting it (WARNING: will also delete objects instancing that speaker data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this speaker data
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this speaker data
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
