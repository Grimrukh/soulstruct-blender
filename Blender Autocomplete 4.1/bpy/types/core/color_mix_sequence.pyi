import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .effect_sequence import EffectSequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ColorMixSequence(EffectSequence, Sequence, bpy_struct):
    """Color Mix Sequence"""

    blend_effect: str
    """ Method for controlling how the strip combines with other strips

    :type: str
    """

    factor: float
    """ Percentage of how much the strip's colors affect other strips

    :type: float
    """

    input_1: Sequence
    """ First input for the effect strip

    :type: Sequence
    """

    input_2: Sequence
    """ Second input for the effect strip

    :type: Sequence
    """

    input_count: int
    """ 

    :type: int
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
