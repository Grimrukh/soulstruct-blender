import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .freestyle_line_style import FreestyleLineStyle
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataLineStyles(bpy_prop_collection[FreestyleLineStyle], bpy_struct):
    """Collection of line styles"""

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    def new(self, name: str | typing.Any) -> FreestyleLineStyle:
        """Add a new line style instance to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New line style data-block
        :rtype: FreestyleLineStyle
        """
        ...

    def remove(
        self,
        linestyle: FreestyleLineStyle,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a line style instance from the current blendfile

        :param linestyle: Line style to remove
        :type linestyle: FreestyleLineStyle
        :param do_unlink: Unlink all usages of this line style before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this line style
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this line style
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
