import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SequenceColorBalanceData(bpy_struct):
    """Color balance parameters for a sequence strip and its modifiers"""

    correction_method: str
    """ 

    :type: str
    """

    gain: mathutils.Color
    """ Color balance gain (highlights)

    :type: mathutils.Color
    """

    gamma: mathutils.Color
    """ Color balance gamma (midtones)

    :type: mathutils.Color
    """

    invert_gain: bool
    """ Invert the gain color

    :type: bool
    """

    invert_gamma: bool
    """ Invert the gamma color

    :type: bool
    """

    invert_lift: bool
    """ Invert the lift color

    :type: bool
    """

    invert_offset: bool
    """ Invert the offset color

    :type: bool
    """

    invert_power: bool
    """ Invert the power color

    :type: bool
    """

    invert_slope: bool
    """ Invert the slope color

    :type: bool
    """

    lift: mathutils.Color
    """ Color balance lift (shadows)

    :type: mathutils.Color
    """

    offset: mathutils.Color
    """ Correction for entire tonal range

    :type: mathutils.Color
    """

    power: mathutils.Color
    """ Correction for midtones

    :type: mathutils.Color
    """

    slope: mathutils.Color
    """ Correction for highlights

    :type: mathutils.Color
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
