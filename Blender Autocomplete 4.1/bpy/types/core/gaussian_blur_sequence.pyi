import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .effect_sequence import EffectSequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GaussianBlurSequence(EffectSequence, Sequence, bpy_struct):
    """Sequence strip creating a gaussian blur"""

    input_1: Sequence
    """ First input for the effect strip

    :type: Sequence
    """

    input_count: int
    """ 

    :type: int
    """

    size_x: float
    """ Size of the blur along X axis

    :type: float
    """

    size_y: float
    """ Size of the blur along Y axis

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
