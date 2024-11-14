import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .sound import Sound

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataSounds(bpy_prop_collection[Sound], bpy_struct):
    """Collection of sounds"""

    def load(
        self,
        filepath: str | typing.Any,
        check_existing: bool | typing.Any | None = False,
    ) -> Sound:
        """Add a new sound to the main database from a file

        :param filepath: path for the data-block
        :type filepath: str | typing.Any
        :param check_existing: Using existing data-block if this file is already loaded
        :type check_existing: bool | typing.Any | None
        :return: New text data-block
        :rtype: Sound
        """
        ...

    def remove(
        self,
        sound: Sound,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a sound from the current blendfile

        :param sound: Sound to remove
        :type sound: Sound
        :param do_unlink: Unlink all usages of this sound before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this sound
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this sound
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
