import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ObjectModifiers(bpy_prop_collection[Modifier], bpy_struct):
    """Collection of object modifiers"""

    active: Modifier | None
    """ The active modifier in the list

    :type: Modifier | None
    """

    def new(self, name: str | typing.Any, type: str | None) -> Modifier:
        """Add a new modifier

        :param name: New name for the modifier
        :type name: str | typing.Any
        :param type: Modifier type to add
        :type type: str | None
        :return: Newly created modifier
        :rtype: Modifier
        """
        ...

    def remove(self, modifier: Modifier):
        """Remove an existing modifier from the object

        :param modifier: Modifier to remove
        :type modifier: Modifier
        """
        ...

    def clear(self):
        """Remove all modifiers from the object"""
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move a modifier to a different position

        :param from_index: From Index, Index to move
        :type from_index: int | None
        :param to_index: To Index, Target index
        :type to_index: int | None
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
