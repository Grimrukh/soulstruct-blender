import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence_modifier import SequenceModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceModifiers(bpy_prop_collection[SequenceModifier], bpy_struct):
    """Collection of strip modifiers"""

    def new(self, name: str | typing.Any, type: str | None) -> SequenceModifier:
        """Add a new modifier

        :param name: New name for the modifier
        :type name: str | typing.Any
        :param type: Modifier type to add
        :type type: str | None
        :return: Newly created modifier
        :rtype: SequenceModifier
        """
        ...

    def remove(self, modifier: SequenceModifier):
        """Remove an existing modifier from the sequence

        :param modifier: Modifier to remove
        :type modifier: SequenceModifier
        """
        ...

    def clear(self):
        """Remove all modifiers from the sequence"""
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
