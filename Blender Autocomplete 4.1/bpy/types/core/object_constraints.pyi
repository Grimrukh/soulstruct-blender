import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ObjectConstraints(bpy_prop_collection[Constraint], bpy_struct):
    """Collection of object constraints"""

    active: Constraint | None
    """ Active Object constraint

    :type: Constraint | None
    """

    def new(self, type: str | None) -> Constraint:
        """Add a new constraint to this object

        :param type: Constraint type to add
        :type type: str | None
        :return: New constraint
        :rtype: Constraint
        """
        ...

    def remove(self, constraint: Constraint):
        """Remove a constraint from this object

        :param constraint: Removed constraint
        :type constraint: Constraint
        """
        ...

    def clear(self):
        """Remove all constraint from this object"""
        ...

    def move(self, from_index: int | None, to_index: int | None):
        """Move a constraint to a different position

        :param from_index: From Index, Index to move
        :type from_index: int | None
        :param to_index: To Index, Target index
        :type to_index: int | None
        """
        ...

    def copy(self, constraint: Constraint) -> Constraint:
        """Add a new constraint that is a copy of the given one

        :param constraint: Constraint to copy - may belong to a different object
        :type constraint: Constraint
        :return: New constraint
        :rtype: Constraint
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
