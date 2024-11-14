import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .constraint_target_bone import ConstraintTargetBone
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ArmatureConstraintTargets(bpy_prop_collection[ConstraintTargetBone], bpy_struct):
    """Collection of target bones and weights"""

    def new(self) -> ConstraintTargetBone:
        """Add a new target to the constraint

        :return: New target bone
        :rtype: ConstraintTargetBone
        """
        ...

    def remove(self, target: ConstraintTargetBone):
        """Delete target from the constraint

        :param target: Target to remove
        :type target: ConstraintTargetBone
        """
        ...

    def clear(self):
        """Delete all targets from object"""
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
