import typing
import collections.abc
import mathutils
from .f_modifier import FModifier
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifierLimits(FModifier, bpy_struct):
    """Limit the time/value ranges of the modified F-Curve"""

    max_x: float
    """ Highest X value to allow

    :type: float
    """

    max_y: float
    """ Highest Y value to allow

    :type: float
    """

    min_x: float
    """ Lowest X value to allow

    :type: float
    """

    min_y: float
    """ Lowest Y value to allow

    :type: float
    """

    use_max_x: bool
    """ Use the maximum X value

    :type: bool
    """

    use_max_y: bool
    """ Use the maximum Y value

    :type: bool
    """

    use_min_x: bool
    """ Use the minimum X value

    :type: bool
    """

    use_min_y: bool
    """ Use the minimum Y value

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
