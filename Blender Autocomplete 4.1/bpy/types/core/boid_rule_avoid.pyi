import typing
import collections.abc
import mathutils
from .struct import Struct
from .boid_rule import BoidRule
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoidRuleAvoid(BoidRule, bpy_struct):
    fear_factor: float
    """ Avoid object if danger from it is above this threshold

    :type: float
    """

    object: Object
    """ Object to avoid

    :type: Object
    """

    use_predict: bool
    """ Predict target movement

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
