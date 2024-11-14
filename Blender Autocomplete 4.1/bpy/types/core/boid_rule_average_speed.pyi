import typing
import collections.abc
import mathutils
from .struct import Struct
from .boid_rule import BoidRule
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoidRuleAverageSpeed(BoidRule, bpy_struct):
    level: float
    """ How much velocity's z-component is kept constant

    :type: float
    """

    speed: float
    """ Percentage of maximum speed

    :type: float
    """

    wander: float
    """ How fast velocity's direction is randomized

    :type: float
    """

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
