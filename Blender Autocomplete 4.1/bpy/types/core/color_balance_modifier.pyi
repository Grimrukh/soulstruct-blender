import typing
import collections.abc
import mathutils
from .struct import Struct
from .sequence_color_balance_data import SequenceColorBalanceData
from .bpy_struct import bpy_struct
from .sequence_modifier import SequenceModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ColorBalanceModifier(SequenceModifier, bpy_struct):
    """Color balance modifier for sequence strip"""

    color_balance: SequenceColorBalanceData
    """ 

    :type: SequenceColorBalanceData
    """

    color_multiply: float
    """ Multiply the intensity of each pixel

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
