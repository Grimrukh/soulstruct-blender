import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .text import Text

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataTexts(bpy_prop_collection[Text], bpy_struct):
    """Collection of texts"""

    def new(self, name: str | typing.Any) -> Text:
        """Add a new text to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New text data-block
        :rtype: Text
        """
        ...

    def remove(
        self,
        text: Text,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a text from the current blendfile

        :param text: Text to remove
        :type text: Text
        :param do_unlink: Unlink all usages of this text before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this text
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this text
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def load(
        self, filepath: str | typing.Any, internal: bool | typing.Any | None = False
    ) -> Text:
        """Add a new text to the main database from a file

        :param filepath: path for the data-block
        :type filepath: str | typing.Any
        :param internal: Make internal, Make text file internal after loading
        :type internal: bool | typing.Any | None
        :return: New text data-block
        :rtype: Text
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
