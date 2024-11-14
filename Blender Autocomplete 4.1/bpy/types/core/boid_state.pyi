import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .boid_rule import BoidRule
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BoidState(bpy_struct):
    """Boid state for boid physics"""

    active_boid_rule: BoidRule
    """ 

    :type: BoidRule
    """

    active_boid_rule_index: int | None
    """ 

    :type: int | None
    """

    falloff: float
    """ 

    :type: float
    """

    name: str
    """ Boid state name

    :type: str
    """

    rule_fuzzy: float
    """ 

    :type: float
    """

    rules: bpy_prop_collection[BoidRule]
    """ 

    :type: bpy_prop_collection[BoidRule]
    """

    ruleset_type: str
    """ How the rules in the list are evaluated

    :type: str
    """

    volume: float
    """ 

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
