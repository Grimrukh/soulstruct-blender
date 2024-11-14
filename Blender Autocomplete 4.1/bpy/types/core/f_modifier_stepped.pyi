import typing
import collections.abc
import mathutils
from .f_modifier import FModifier
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FModifierStepped(FModifier, bpy_struct):
    """Hold each interpolated value from the F-Curve for several frames without changing the timing"""

    frame_end: float
    """ Frame that modifier's influence ends (if applicable)

    :type: float
    """

    frame_offset: float
    """ Reference number of frames before frames get held (use to get hold for '1-3' vs '5-7' holding patterns)

    :type: float
    """

    frame_start: float
    """ Frame that modifier's influence starts (if applicable)

    :type: float
    """

    frame_step: float
    """ Number of frames to hold each value

    :type: float
    """

    use_frame_end: bool
    """ Restrict modifier to only act before its 'end' frame

    :type: bool
    """

    use_frame_start: bool
    """ Restrict modifier to only act after its 'start' frame

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
