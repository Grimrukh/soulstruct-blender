import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .vector_font import VectorFont
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataFonts(bpy_prop_collection[VectorFont], bpy_struct):
    """Collection of fonts"""

    def load(
        self,
        filepath: str | typing.Any,
        check_existing: bool | typing.Any | None = False,
    ) -> VectorFont:
        """Load a new font into the main database

        :param filepath: path of the font to load
        :type filepath: str | typing.Any
        :param check_existing: Using existing data-block if this file is already loaded
        :type check_existing: bool | typing.Any | None
        :return: New font data-block
        :rtype: VectorFont
        """
        ...

    def remove(
        self,
        vfont: VectorFont,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a font from the current blendfile

        :param vfont: Font to remove
        :type vfont: VectorFont
        :param do_unlink: Unlink all usages of this font before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this font
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this font
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
