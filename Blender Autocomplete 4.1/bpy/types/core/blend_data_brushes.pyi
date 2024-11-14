import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .brush import Brush

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataBrushes(bpy_prop_collection[Brush], bpy_struct):
    """Collection of brushes"""

    def new(self, name: str | typing.Any, mode: str | None = "TEXTURE_PAINT") -> Brush:
        """Add a new brush to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param mode: Paint Mode for the new brush
        :type mode: str | None
        :return: New brush data-block
        :rtype: Brush
        """
        ...

    def remove(
        self,
        brush: Brush,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a brush from the current blendfile

        :param brush: Brush to remove
        :type brush: Brush
        :param do_unlink: Unlink all usages of this brush before deleting it
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this brush
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this brush
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
        """
        ...

    def create_gpencil_data(self, brush: Brush):
        """Add grease pencil brush settings

        :param brush: Brush
        :type brush: Brush
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
