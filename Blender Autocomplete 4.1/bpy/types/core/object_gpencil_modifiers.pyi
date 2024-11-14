import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ObjectGpencilModifiers(bpy_prop_collection[GpencilModifier], bpy_struct):
    """Collection of object grease pencil modifiers"""

    def new(self, name: str | typing.Any, type: str | None) -> GpencilModifier:
        """Add a new greasepencil_modifier

        :param name: New name for the greasepencil_modifier
        :type name: str | typing.Any
        :param type: Modifier type to add
        :type type: str | None
        :return: Newly created modifier
        :rtype: GpencilModifier
        """
        ...

    def remove(self, greasepencil_modifier: GpencilModifier):
        """Remove an existing greasepencil_modifier from the object

        :param greasepencil_modifier: Modifier to remove
        :type greasepencil_modifier: GpencilModifier
        """
        ...

    def clear(self):
        """Remove all grease pencil modifiers from the object"""
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
