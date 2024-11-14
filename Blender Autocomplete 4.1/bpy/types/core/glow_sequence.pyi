import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .sequence import Sequence
from .effect_sequence import EffectSequence

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GlowSequence(EffectSequence, Sequence, bpy_struct):
    """Sequence strip creating a glow effect"""

    blur_radius: float
    """ Radius of glow effect

    :type: float
    """

    boost_factor: float
    """ Brightness multiplier

    :type: float
    """

    clamp: float
    """ Brightness limit of intensity

    :type: float
    """

    input_1: Sequence
    """ First input for the effect strip

    :type: Sequence
    """

    input_count: int
    """ 

    :type: int
    """

    quality: int
    """ Accuracy of the blur effect

    :type: int
    """

    threshold: float
    """ Minimum intensity to trigger a glow

    :type: float
    """

    use_only_boost: bool
    """ Show the glow buffer only

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
