import typing
import collections.abc
import mathutils
from .f_modifier import FModifier
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifierNoise(FModifier, bpy_struct):
    """Give randomness to the modified F-Curve"""

    blend_type: str
    """ Method of modifying the existing F-Curve

    :type: str
    """

    depth: int
    """ Amount of fine level detail present in the noise

    :type: int
    """

    offset: float
    """ Time offset for the noise effect

    :type: float
    """

    phase: float
    """ A random seed for the noise effect

    :type: float
    """

    scale: float
    """ Scaling (in time) of the noise

    :type: float
    """

    strength: float
    """ Amplitude of the noise - the amount that it modifies the underlying curve

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
