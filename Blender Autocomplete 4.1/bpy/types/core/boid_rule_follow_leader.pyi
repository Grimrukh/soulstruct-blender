import typing
import collections.abc
import mathutils
from .struct import Struct
from .boid_rule import BoidRule
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoidRuleFollowLeader(BoidRule, bpy_struct):
    distance: float
    """ Distance behind leader to follow

    :type: float
    """

    object: Object
    """ Follow this object instead of a boid

    :type: Object
    """

    queue_count: int
    """ How many boids in a line

    :type: int
    """

    use_line: bool
    """ Follow leader in a line

    :type: bool
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
