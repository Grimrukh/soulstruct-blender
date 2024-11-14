import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .f_modifier import FModifier
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FCurveModifiers(bpy_prop_collection[FModifier], bpy_struct):
    """Collection of F-Curve Modifiers"""

    active: FModifier | None
    """ Active F-Curve Modifier

    :type: FModifier | None
    """

    def new(self, type: str | None) -> FModifier:
        """Add a constraint to this object

        :param type: Constraint type to add
        :type type: str | None
        :return: New fmodifier
        :rtype: FModifier
        """
        ...

    def remove(self, modifier: FModifier):
        """Remove a modifier from this F-Curve

        :param modifier: Removed modifier
        :type modifier: FModifier
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
